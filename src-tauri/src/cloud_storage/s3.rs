use std::collections::BTreeMap;
use chrono::Utc;
use hmac::{Hmac, Mac};
use sha2::{Digest, Sha256};
use crate::models::{CloudBackupItem, S3Config};

type HmacSha256 = Hmac<Sha256>;

pub struct S3Client {
    pub config: S3Config,
    pub http_client: reqwest::Client,
}

impl S3Client {
    pub fn new(config: S3Config) -> Self {
        let http_client = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(15))
            .build()
            .unwrap_or_default();
        Self { config, http_client }
    }

    fn sha256_hex(data: &[u8]) -> String {
        let mut hasher = Sha256::new();
        hasher.update(data);
        hex::encode(hasher.finalize())
    }

    fn hmac_sha256(key: &[u8], data: &[u8]) -> Vec<u8> {
        let mut mac = HmacSha256::new_from_slice(key).expect("HMAC key length valid");
        mac.update(data);
        mac.finalize().into_bytes().to_vec()
    }

    fn get_signing_key(&self, date_stamp: &str) -> Vec<u8> {
        let k_secret = format!("AWS4{}", self.config.secret_key);
        let k_date = Self::hmac_sha256(k_secret.as_bytes(), date_stamp.as_bytes());
        let k_region = Self::hmac_sha256(&k_date, self.config.region.as_bytes());
        let k_service = Self::hmac_sha256(&k_region, b"s3");
        Self::hmac_sha256(&k_service, b"aws4_request")
    }

    /// 执行 AWS Signature Version 4 签名计算并注入请求头
    fn sign_request(
        &self,
        method: &str,
        path: &str,
        query: &str,
        payload: &[u8],
        headers_in: &mut reqwest::header::HeaderMap,
    ) {
        let now = Utc::now();
        let amz_date = now.format("%Y%m%dT%H%M%SZ").to_string();
        let date_stamp = now.format("%Y%m%d").to_string();
        let payload_hash = Self::sha256_hex(payload);

        let endpoint_url = self.config.endpoint.trim_end_matches('/');
        let host = if let Ok(u) = reqwest::Url::parse(endpoint_url) {
            u.host_str().unwrap_or("").to_string()
        } else {
            endpoint_url.to_string()
        };

        headers_in.insert("host", host.parse().unwrap());
        headers_in.insert("x-amz-date", amz_date.parse().unwrap());
        headers_in.insert("x-amz-content-sha256", payload_hash.parse().unwrap());

        let mut sorted_headers = BTreeMap::new();
        for (k, v) in headers_in.iter() {
            sorted_headers.insert(k.as_str().to_lowercase(), v.to_str().unwrap_or("").trim().to_string());
        }

        let signed_headers = sorted_headers.keys().cloned().collect::<Vec<_>>().join(";");
        let mut canonical_headers = String::new();
        for (k, v) in &sorted_headers {
            canonical_headers.push_str(&format!("{}:{}\n", k, v));
        }

        let canonical_uri = if path.starts_with('/') { path.to_string() } else { format!("/{}", path) };
        let canonical_request = format!(
            "{}\n{}\n{}\n{}\n{}\n{}",
            method,
            canonical_uri,
            query,
            canonical_headers,
            signed_headers,
            payload_hash
        );

        let canonical_request_hash = Self::sha256_hex(canonical_request.as_bytes());
        let credential_scope = format!("{}/{}/s3/aws4_request", date_stamp, self.config.region);
        let string_to_sign = format!(
            "AWS4-HMAC-SHA256\n{}\n{}\n{}",
            amz_date,
            credential_scope,
            canonical_request_hash
        );

        let signing_key = self.get_signing_key(&date_stamp);
        let signature = hex::encode(Self::hmac_sha256(&signing_key, string_to_sign.as_bytes()));

        let auth_header = format!(
            "AWS4-HMAC-SHA256 Credential={}/{}, SignedHeaders={}, Signature={}",
            self.config.access_key,
            credential_scope,
            signed_headers,
            signature
        );

        headers_in.insert("authorization", auth_header.parse().unwrap());
    }

    fn get_normalized_endpoint(&self) -> String {
        let trimmed = self.config.endpoint.trim();
        if trimmed.starts_with("http://") || trimmed.starts_with("https://") {
            trimmed.trim_end_matches('/').to_string()
        } else {
            format!("https://{}", trimmed.trim_end_matches('/'))
        }
    }

    fn build_url(&self, key: &str) -> (String, String) {
        let endpoint = self.get_normalized_endpoint();
        let bucket = self.config.bucket.trim();
        let clean_key = key.trim_start_matches('/');
        let path = if clean_key.is_empty() {
            format!("/{}", bucket)
        } else {
            format!("/{}/{}", bucket, clean_key)
        };
        (format!("{}{}", endpoint, path), path)
    }

    pub async fn test_connection(&self) -> Result<String, String> {
        let (full_url, path) = self.build_url("");
        let query = "list-type=2&max-keys=1";
        let req_url = format!("{}?{}", full_url, query);

        let mut headers = reqwest::header::HeaderMap::new();
        self.sign_request("GET", &path, query, &[], &mut headers);

        let resp = self.http_client.get(&req_url)
            .headers(headers)
            .send()
            .await
            .map_err(|e| format!("网络请求失败: {}", e))?;

        if resp.status().is_success() {
            Ok(format!("S3/R2 存储桶 [{}] 连接正常，读写鉴权通过！", self.config.bucket))
        } else {
            let status = resp.status();
            let body = resp.text().await.unwrap_or_default();
            Err(format!("S3 返回状态码 {}: {}", status, body))
        }
    }

    pub async fn upload(&self, key_name: &str, data: &[u8]) -> Result<(), String> {
        let full_key = format!("{}{}", self.config.prefix, key_name);
        let (full_url, path) = self.build_url(&full_key);

        let mut headers = reqwest::header::HeaderMap::new();
        headers.insert("content-type", "application/json".parse().unwrap());
        self.sign_request("PUT", &path, "", data, &mut headers);

        let resp = self.http_client.put(&full_url)
            .headers(headers)
            .body(data.to_vec())
            .send()
            .await
            .map_err(|e| format!("上传失败: {}", e))?;

        if resp.status().is_success() {
            Ok(())
        } else {
            let status = resp.status();
            let body = resp.text().await.unwrap_or_default();
            Err(format!("S3 上传返回错误 {}: {}", status, body))
        }
    }

    pub async fn download(&self, key_name: &str) -> Result<Vec<u8>, String> {
        let full_key = format!("{}{}", self.config.prefix, key_name);
        let (full_url, path) = self.build_url(&full_key);

        let mut headers = reqwest::header::HeaderMap::new();
        self.sign_request("GET", &path, "", &[], &mut headers);

        let resp = self.http_client.get(&full_url)
            .headers(headers)
            .send()
            .await
            .map_err(|e| format!("下载失败: {}", e))?;

        if resp.status().is_success() {
            resp.bytes().await.map(|b| b.to_vec()).map_err(|e| format!("读取内容失败: {}", e))
        } else {
            let status = resp.status();
            let body = resp.text().await.unwrap_or_default();
            Err(format!("S3 下载返回错误 {}: {}", status, body))
        }
    }

    pub async fn delete(&self, key_name: &str) -> Result<(), String> {
        let full_key = format!("{}{}", self.config.prefix, key_name);
        let (full_url, path) = self.build_url(&full_key);

        let mut headers = reqwest::header::HeaderMap::new();
        self.sign_request("DELETE", &path, "", &[], &mut headers);

        let resp = self.http_client.delete(&full_url)
            .headers(headers)
            .send()
            .await
            .map_err(|e| format!("删除失败: {}", e))?;

        if resp.status().is_success() || resp.status().as_u16() == 204 {
            Ok(())
        } else {
            let status = resp.status();
            let body = resp.text().await.unwrap_or_default();
            Err(format!("S3 删除返回错误 {}: {}", status, body))
        }
    }

    pub async fn list_backups(&self) -> Result<Vec<CloudBackupItem>, String> {
        let (full_url, path) = self.build_url("");
        let query = format!("list-type=2&prefix={}", self.config.prefix);
        let req_url = format!("{}?{}", full_url, query);

        let mut headers = reqwest::header::HeaderMap::new();
        self.sign_request("GET", &path, &query, &[], &mut headers);

        let resp = self.http_client.get(&req_url)
            .headers(headers)
            .send()
            .await
            .map_err(|e| format!("获取备份列表失败: {}", e))?;

        if !resp.status().is_success() {
            let status = resp.status();
            let body = resp.text().await.unwrap_or_default();
            return Err(format!("列举对象失败 {}: {}", status, body));
        }

        let xml = resp.text().await.unwrap_or_default();
        let mut items = Vec::new();

        // 正则提取 S3 ListObjectsV2 返回的 <Contents> 节点
        let key_re = regex::Regex::new(r"<Key>(.*?)</Key>").unwrap();
        let size_re = regex::Regex::new(r"<Size>(\d+)</Size>").unwrap();
        let lm_re = regex::Regex::new(r"<LastModified>(.*?)</LastModified>").unwrap();

        let contents_re = regex::Regex::new(r"(?s)<Contents>(.*?)</Contents>").unwrap();

        for cap in contents_re.captures_iter(&xml) {
            let block = &cap[1];
            if let Some(k) = key_re.captures(block).and_then(|c| c.get(1)) {
                let full_key = k.as_str();
                let file_name = full_key.trim_start_matches(&self.config.prefix).to_string();
                if !file_name.starts_with("zcode-backup-") || !file_name.ends_with(".json") {
                    continue;
                }

                let size_bytes: u64 = size_re.captures(block)
                    .and_then(|c| c.get(1))
                    .and_then(|s| s.as_str().parse().ok())
                    .unwrap_or(0);

                let last_modified = lm_re.captures(block)
                    .and_then(|c| c.get(1))
                    .map(|s| s.as_str().to_string())
                    .unwrap_or_default();

                items.push(CloudBackupItem {
                    name: file_name,
                    size_bytes,
                    last_modified,
                    provider_count: 0,
                });
            }
        }

        items.sort_by(|a, b| b.name.cmp(&a.name));
        Ok(items)
    }
}
