/**
 * Cordova Web Mock para Desktop
 * Substitui o runtime nativo do Android por mocks limpos que não bloqueiam a execução no navegador.
 */
console.log("[s_ADB_Tools] Cordova Web Mock ativo.");

window.cordova = window.cordova || {};
window.cordova.platformId = "browser";
window.cordova.version = "1.0.0";
window.cordova.file = { dataDirectory: "" };
window.cordova.plugins = window.cordova.plugins || {};
window.plugins = window.plugins || {};
