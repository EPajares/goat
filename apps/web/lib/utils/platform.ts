type DeviceInfo = {
    isMac: boolean;
    isWindows: boolean;
    isLinux: boolean;
    isTouchDevice: boolean;
    isMobile: boolean;
    getModShortcutKey: () => string;
};

let cachedDeviceInfo: DeviceInfo | undefined;

/**
 * Returns a comprehensive device info object with cached values.
 * Safe for SSR and modern/legacy browsers.
 */
export function getDeviceInfo(): DeviceInfo {
    if (cachedDeviceInfo) return cachedDeviceInfo;

    const isBrowser = typeof window !== "undefined" && typeof navigator !== "undefined";

    // Default values for non-browser environments
    let platform = "";
    let userAgent = "";
    let isTouchDevice = false;

    if (isBrowser) {
        // Prefer modern userAgentData API
        const nav = navigator as Navigator & { userAgentData?: { platform?: string } };
        platform = nav.userAgentData?.platform || navigator.platform || "";
        userAgent = navigator.userAgent || "";

        // Modern touch detection
        isTouchDevice = "ontouchstart" in window || navigator.maxTouchPoints > 0;
    }

    const isMac = /Mac/i.test(platform) || /Macintosh|Mac OS X/i.test(userAgent);
    const isWindows = /Win/i.test(platform) || /Windows/i.test(userAgent);
    const isLinux = /Linux/i.test(platform);

    // Include phones and tablets (iPad, Android tablets, etc.)
    const isMobile =
        isBrowser &&
        (/Mobi/i.test(userAgent) || /iPad|Tablet|Android/i.test(userAgent));

    cachedDeviceInfo = {
        isMac,
        isWindows,
        isLinux,
        isTouchDevice,
        isMobile,
        getModShortcutKey: () => (isMac ? "⌘" : "Ctrl"),
    };

    return cachedDeviceInfo;
}

/** Shortcut helpers */
export const isMac = () => getDeviceInfo().isMac;
export const isWindows = () => getDeviceInfo().isWindows;
export const isLinux = () => getDeviceInfo().isLinux;
export const isTouchDevice = () => getDeviceInfo().isTouchDevice;
export const isMobile = () => getDeviceInfo().isMobile;
export const getModShortcutKey = () => getDeviceInfo().getModShortcutKey();
