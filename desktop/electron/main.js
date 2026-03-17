/**
 * VICTOR-SSI Electron Desktop Wrapper
 * Creates a BrowserWindow and loads the gateway URL.
 *
 * Environment variables (set before launching):
 *   GATEWAY_URL  - URL of the API gateway (default: http://localhost:8080)
 */

const { app, BrowserWindow, shell } = require("electron");
const path = require("path");

const GATEWAY_URL = process.env.GATEWAY_URL || "http://localhost:8080";

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    title: "VICTOR-SSI — Aether Hub",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: undefined,
    },
    icon: path.join(__dirname, "assets", "icon.png"),
  });

  win.loadURL(GATEWAY_URL);

  // Open external links in the default browser instead of Electron
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
