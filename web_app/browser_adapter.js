/**
 * Adaptador de Compatibilidade para Execução no Navegador Desktop
 * Simula as APIs e plugins nativos do Apache Cordova usando recursos do navegador padrão.
 */

window.G_IsDebugging = 1;
window.G_ShowAds = 0;
window.G_TestingAds = false;

// Mock Cordova Core
window.cordova = window.cordova || {};
window.cordova.file = window.cordova.file || { dataDirectory: "" };
window.cordova.plugins = window.cordova.plugins || {};
window.plugins = window.plugins || {};

// Mock Diagnostic Plugin
window.cordova.plugins.diagnostic = window.cordova.plugins.diagnostic || {
    getDeviceOSVersion: function(cb) {
        if (typeof cb === "function") cb({ os: "Desktop Browser", version: "1.0" });
    },
    isCameraAuthorized: function(cb) {
        if (typeof cb === "function") cb(true);
    },
    requestCameraAuthorization: function(cb) {
        if (typeof cb === "function") cb("GRANTED");
    }
};

// Mock StatusBar
window.StatusBar = window.StatusBar || {
    hide: function() {},
    show: function() {}
};

// Mock Notifications & Dialogs
window.navigator.notification = window.navigator.notification || {
    alert: function(message, callback, title) {
        alert((title ? title + "\n\n" : "") + message);
        if (typeof callback === "function") callback();
    },
    confirm: function(message, callback, title, buttons) {
        var res = confirm((title ? title + "\n\n" : "") + message);
        if (typeof callback === "function") callback(res ? 1 : 2);
    },
    beep: function() {}
};

// Mock File System Plugin -> Fallback amigável para localStorage
window.resolveLocalFileSystemURL = window.resolveLocalFileSystemURL || function(path, ok, err) {
    if (typeof err === "function") {
        err(new Error("Ambiente Web Desktop: persistência ativa via localStorage."));
    }
};

// Polyfill para disparar o ciclo de vida deviceready
document.addEventListener("DOMContentLoaded", function() {
    setTimeout(function() {
        var evt;
        try {
            evt = new CustomEvent("deviceready", { bubbles: false, cancelable: false });
        } catch (e) {
            evt = document.createEvent("Events");
            evt.initEvent("deviceready", false, false);
        }
        document.dispatchEvent(evt);
        console.log("[s_ADB_Tools] Adaptador Web Carregado: Aplicação pronta para uso no navegador!");
    }, 150);
});
