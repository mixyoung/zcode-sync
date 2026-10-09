use crate::models::{CloudBackupItem, WebDavConfig};

pub struct WebDavClient {
    pub config: WebDavConfig,
    pub http_client: reqwest::Client,
}

impl WebDavClient {
    pub fn new(config: WebDavConfig) -> Self {
        let http_client = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(15))
            .build()
            .unwrap_or_default();
        Self { config, http_client }
    }

    fn get_normalized_base(&self) -> String {
        let trimmed = self.config.server_url.trim();
        if trimmed.starts_with("http://") || trimmed.starts_with("https://") {
            trimmed.trim_end_matches('/').to_string()
        } else {
            format!("https://{}", trimmed.trim_end_matches('/'))
        }
    }

    fn build_file_url(&self, file_name: &str) -> String {
        let base = self.get_normalized_base();
        let r_dir = self.config.remote_dir.trim_matches('/');
        if r_dir.is_empty() {
            format!("{}/{}", base, file_name.trim_start_matches('/'))
        } else {
            format!("{}/{}/{}", base, r_dir, file_name.trim_start_matches('/'))
        }
    }

    fn build_dir_url(&self) -> String {
        let base = self.get_normalized_base();
        let r_dir = self.config.remote_dir.trim_matches('/');
        if r_dir.is_empty() {
            format!("{}/", base)
        } else {
            format!("{}/{}/", base, r_dir)
        }
    }

    pub async fn ensure_dir(&self) -> Result<(), String> {
        let dir_url = self.build_dir_url();
        let resp = self.http_client
            .request(reqwest::Method::from_bytes(b"MKCOL").unwrap(), &dir_url)
            .basic_auth(&self.config.username, Some(&self.config.password))
            .send()
            .await
            .map_err(|e| format!("创建远端目录失败: {}", e))?;

        // 201 Created 或 405 Method Not Allowed (说明目录已存在) 均为正常
        if resp.status().is_success() || resp.status().as_u16() == 405 {
            Ok(())
        } else {
            Err(format!("WebDAV 创建目录状态: {}", resp.status()))
        }
    }

    pub async fn test_connection(&self) -> Result<String, String> {
        let _ = self.ensure_dir().await;
        let dir_url = self.build_dir_url();

        let resp = self.http_client
            .request(reqwest::Method::from_bytes(b"PROPFIND").unwrap(), &dir_url)
            .basic_auth(&self.config.username, Some(&self.config.password))
            .header("Depth", "0")
            .send()
            .await
            .map_err(|e| format!("连接 WebDAV 失败: {}", e))?;

        if resp.status().is_success() || resp.status().as_u16() == 207 {
            Ok(format!("WebDAV 服务器 [{}] 连接正常，目录鉴权通过！", self.config.server_url))
        } else {
            Err(format!("WebDAV 认证失败，状态码: {}", resp.status()))
        }
    }

    pub async fn upload(&self, file_name: &str, data: &[u8]) -> Result<(), String> {
        let _ = self.ensure_dir().await;
        let file_url = self.build_file_url(file_name);

        let resp = self.http_client
            .put(&file_url)
            .basic_auth(&self.config.username, Some(&self.config.password))
            .header("Content-Type", "application/json")
            .body(data.to_vec())
            .send()
            .await
            .map_err(|e| format!("上传文件失败: {}", e))?;

        if resp.status().is_success() || resp.status().as_u16() == 201 || resp.status().as_u16() == 204 {
            Ok(())
        } else {
            Err(format!("WebDAV 上传状态码: {}", resp.status()))
        }
    }

    pub async fn download(&self, file_name: &str) -> Result<Vec<u8>, String> {
        let file_url = self.build_file_url(file_name);

        let resp = self.http_client
            .get(&file_url)
            .basic_auth(&self.config.username, Some(&self.config.password))
            .send()
            .await
            .map_err(|e| format!("下载失败: {}", e))?;

        if resp.status().is_success() {
            resp.bytes().await.map(|b| b.to_vec()).map_err(|e| format!("读取内容失败: {}", e))
        } else {
            Err(format!("WebDAV 下载状态码: {}", resp.status()))
        }
    }

    pub async fn delete(&self, file_name: &str) -> Result<(), String> {
        let file_url = self.build_file_url(file_name);

        let resp = self.http_client
            .delete(&file_url)
            .basic_auth(&self.config.username, Some(&self.config.password))
            .send()
            .await
            .map_err(|e| format!("删除失败: {}", e))?;

        if resp.status().is_success() || resp.status().as_u16() == 204 {
            Ok(())
        } else {
            Err(format!("WebDAV 删除状态码: {}", resp.status()))
        }
    }

    pub async fn list_backups(&self) -> Result<Vec<CloudBackupItem>, String> {
        let _ = self.ensure_dir().await;
        let dir_url = self.build_dir_url();

        let resp = self.http_client
            .request(reqwest::Method::from_bytes(b"PROPFIND").unwrap(), &dir_url)
            .basic_auth(&self.config.username, Some(&self.config.password))
            .header("Depth", "1")
            .send()
            .await
            .map_err(|e| format!("获取列表失败: {}", e))?;

        if !resp.status().is_success() && resp.status().as_u16() != 207 {
            return Err(format!("PROPFIND 返回状态: {}", resp.status()));
        }

        let xml = resp.text().await.unwrap_or_default();
        let mut items = Vec::new();

        let response_re = regex::Regex::new(r"(?is)<(?:\w+:)?response>(.*?)</(?:\w+:)?response>").unwrap();
        let href_re = regex::Regex::new(r"(?i)<(?:\w+:)?href>(.*?)</(?:\w+:)?href>").unwrap();
        let length_re = regex::Regex::new(r"(?i)<(?:\w+:)?getcontentlength>(\d+)</(?:\w+:)?getcontentlength>").unwrap();
        let modified_re = regex::Regex::new(r"(?i)<(?:\w+:)?getlastmodified>(.*?)</(?:\w+:)?getlastmodified>").unwrap();

        for cap in response_re.captures_iter(&xml) {
            let block = &cap[1];
            if let Some(href) = href_re.captures(block).and_then(|c| c.get(1)) {
                let href_val = href.as_str();
                let file_name = href_val.trim_end_matches('/').split('/').last().unwrap_or("").to_string();

                if !file_name.starts_with("zcode-backup-") || !file_name.ends_with(".json") {
                    continue;
                }

                let size_bytes: u64 = length_re.captures(block)
                    .and_then(|c| c.get(1))
                    .and_then(|s| s.as_str().parse().ok())
                    .unwrap_or(0);

                let last_modified = modified_re.captures(block)
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
