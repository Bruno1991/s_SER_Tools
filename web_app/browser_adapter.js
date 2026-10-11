/**
 * Adaptador de Compatibilidade para Execução no Navegador Desktop
 * Simula as APIs e plugins nativos do Apache Cordova usando recursos do navegador padrão.
 */

console.log("[s_ADB_Tools] Carregando Adaptador Web Desktop...");

window.G_IsDebugging = 1;
window.G_ShowAds = 0;
window.G_TestingAds = false;
window.G_WasBannerShowed = 1;
window.G_InterstitialShowed = 1;

// Mock AdMob Plus Plugin
window.admob = window.admob || {
    BannerAd: function() {
        this.show = function() {};
        this.hide = function() {};
    },
    InterstitialAd: function() {
        this.load = function() {};
        this.show = function() {};
    }
};

// Mock Consent / GDPR Plugin
window.consent = window.consent || {
    requestInfoUpdate: async function() {},
    getConsentStatus: async function() { return "NOT_REQUIRED"; },
    getFormStatus: async function() { return "UNAVAILABLE"; },
    loadForm: async function() { return { show: function() {} }; },
    ConsentStatus: { Required: 1, Unknown: 2, NotRequired: 3 },
    FormStatus: { Available: 1, Unavailable: 2 }
};

// Mock FileError do Cordova (evita ReferenceError em errorHandler)
window.FileError = window.FileError || {
    NOT_FOUND_ERR: 1,
    SECURITY_ERR: 2,
    ABORT_ERR: 3,
    NOT_READABLE_ERR: 4,
    ENCODING_ERR: 5,
    NO_MODIFICATION_ALLOWED_ERR: 6,
    INVALID_STATE_ERR: 7,
    SYNTAX_ERR: 8,
    INVALID_MODIFICATION_ERR: 9,
    QUOTA_EXCEEDED_ERR: 10,
    TYPE_MISMATCH_ERR: 11,
    PATH_EXISTS_ERR: 12
};

// Mock Cordova Core
window.cordova = window.cordova || {};
window.cordova.platformId = "browser";
window.cordova.file = { dataDirectory: "" };
window.cordova.plugins = window.cordova.plugins || {};
window.plugins = window.plugins || {};

// Mock Diagnostic Plugin
window.diagnostic = {
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
window.cordova.plugins.diagnostic = window.diagnostic;

// Mock StatusBar
window.StatusBar = window.StatusBar || {
    hide: function() {},
    show: function() {}
};

// Mock Splashscreen
window.navigator.splashscreen = window.navigator.splashscreen || {
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

// Mock File System Plugin -> No-op seguro (a aplicação usa localStorage primariamente)
window.resolveLocalFileSystemURL = function(path, successCallback, errorCallback) {
    // Modo Web puro: não grava arquivos físicos locais, mantendo 100% no localStorage
};

console.log("[s_ADB_Tools] Adaptador Web Desktop pronto!");
