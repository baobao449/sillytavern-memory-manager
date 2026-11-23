// Plugin preferences are shared; source-floor cursors always belong to a chat.
export const CHAT_PROGRESS_KEYS = new Set(['startFloor', 'autoStartFloor']);
export const SHARED_SETTINGS_SCOPE = 'global-v1';

export function migrateSharedSettings(global, saved, defaults, legacyGlobalKeys, schema) {
 if (global.settingsScope === SHARED_SETTINGS_SCOPE) return false;
 // Adopt the active chat once, so upgrading keeps the settings the user was using.
 if (saved?.settingsSchema === schema) {
  for (const key of Object.keys(defaults)) {
   if (!CHAT_PROGRESS_KEYS.has(key) && !legacyGlobalKeys.has(key) && key !== 'worldBooks' && saved[key] !== undefined) global[key] = structuredClone(saved[key]);
  }
 }
 global.settingsScope = SHARED_SETTINGS_SCOPE;
 return true;
}

export function chatProgress(value, schema) {
 return {settingsSchema: schema, ...Object.fromEntries([...CHAT_PROGRESS_KEYS].map(key => [key, Math.max(0, Number(value?.[key]) || 0)]))};
}
