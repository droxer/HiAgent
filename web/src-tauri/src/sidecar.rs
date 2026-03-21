use std::path::Path;
use std::process::Stdio;
use std::time::Duration;
use tokio::process::{Child, Command};
use tokio::time::sleep;

/// Manages the lifecycle of backend and frontend sidecar processes.
pub struct SidecarManager {
    backend: Option<Child>,
    frontend: Option<Child>,
}

impl SidecarManager {
    pub fn new() -> Self {
        Self {
            backend: None,
            frontend: None,
        }
    }

    /// Start the Python FastAPI backend.
    pub async fn start_backend(
        &mut self,
        project_dir: &Path,
        port: u16,
    ) -> Result<(), String> {
        let backend_dir = project_dir.join("backend");
        log::info!("Starting backend in {:?} on port {port}", backend_dir);

        let child = Command::new("uv")
            .args(["run", "python", "-m", "api.main"])
            .env("PORT", port.to_string())
            .current_dir(&backend_dir)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .kill_on_drop(true)
            .spawn()
            .map_err(|e| format!("Failed to start backend: {e}"))?;

        self.backend = Some(child);
        self.wait_healthy(port, Duration::from_secs(30)).await?;
        log::info!("Backend is healthy on port {port}");
        Ok(())
    }

    /// Start the Next.js frontend.
    pub async fn start_frontend(
        &mut self,
        project_dir: &Path,
        port: u16,
    ) -> Result<(), String> {
        let web_dir = project_dir.join("web");
        log::info!("Starting frontend in {:?} on port {port}", web_dir);

        let child = Command::new("npm")
            .args(["run", "dev", "--", "--port", &port.to_string()])
            .current_dir(&web_dir)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .kill_on_drop(true)
            .spawn()
            .map_err(|e| format!("Failed to start frontend: {e}"))?;

        self.frontend = Some(child);
        self.wait_healthy(port, Duration::from_secs(30)).await?;
        log::info!("Frontend is healthy on port {port}");
        Ok(())
    }

    /// Poll a local port until it responds with HTTP 200, or time out.
    async fn wait_healthy(&self, port: u16, timeout: Duration) -> Result<(), String> {
        let url = format!("http://localhost:{port}");
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(2))
            .build()
            .map_err(|e| format!("Failed to create HTTP client: {e}"))?;

        let deadline = tokio::time::Instant::now() + timeout;

        loop {
            if tokio::time::Instant::now() > deadline {
                return Err(format!(
                    "Timed out waiting for service on port {port} after {timeout:?}"
                ));
            }

            match client.get(&url).send().await {
                Ok(resp) if resp.status().is_success() || resp.status().is_redirection() => {
                    return Ok(());
                }
                _ => {
                    sleep(Duration::from_millis(500)).await;
                }
            }
        }
    }

    /// Check whether a port is already in use.
    pub async fn is_port_in_use(port: u16) -> bool {
        tokio::net::TcpStream::connect(format!("127.0.0.1:{port}"))
            .await
            .is_ok()
    }

    /// Gracefully shut down all sidecar processes.
    pub async fn shutdown(&mut self) {
        if let Some(ref mut child) = self.frontend {
            log::info!("Shutting down frontend");
            let _ = child.kill().await;
        }
        self.frontend = None;

        if let Some(ref mut child) = self.backend {
            log::info!("Shutting down backend");
            let _ = child.kill().await;
        }
        self.backend = None;
    }
}

impl Drop for SidecarManager {
    fn drop(&mut self) {
        if let Some(ref mut child) = self.frontend {
            let _ = child.start_kill();
        }
        if let Some(ref mut child) = self.backend {
            let _ = child.start_kill();
        }
    }
}
