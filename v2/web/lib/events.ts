export const APP_DATA_CHANGED = "app:data-changed";

export function notifyDataChanged() {
    if (typeof window === "undefined") return;
    window.dispatchEvent(new Event(APP_DATA_CHANGED));
}
