import Cocoa
import ApplicationServices

// システム設定のURLスキームでVPN画面を開く
let url = URL(string: "x-apple.systempreferences:com.apple.preferences.network?VPN")!
NSWorkspace.shared.open(url)

// UI描画を待機
Thread.sleep(forTimeInterval: 3.0)

// システム設定アプリのAXUIElementを取得
let systemPrefsPID = NSWorkspace.shared.runningApplications.first { $0.bundleIdentifier == "com.apple.systempreferences" }?.processIdentifier
guard let pid = systemPrefsPID else {
    print("{\"status\": \"UNKNOWN\", \"error\": \"System Settings not running\"}")
    exit(1)
}

let appElement = AXUIElementCreateApplication(pid)

// UIツリーからVPNの状態テキストを再帰的に検索する関数
func findVpnStatus(element: AXUIElement, depth: Int = 0) -> (de: String, us: String)? {
    var childrenRef: CFArray?
    let result = AXUIElementCopyAttributeValues(element, kAXChildrenAttribute as CFString, 0, 10, &childrenRef)

    if result == .success, let children = childrenRef as? [AXUIElement] {
        for child in children {
            var titleRef: CFTypeRef?
            AXUIElementCopyAttributeValue(child, kAXTitleAttribute as CFString, &titleRef)
            var valueRef: CFTypeRef?
            AXUIElementCopyAttributeValue(child, kAXValueAttribute as CFString, &valueRef)

            let title = titleRef as? String ?? ""
            let value = valueRef as? String ?? ""

            // スイッチの値(1/0)やテキストから状態を推測
            if title.contains("AHC DE") || value.contains("AHC DE") {
                // 親要素や兄弟要素から接続状態を探す (簡易実装)
                let status = value.contains("Connected") || value == "1" ? "UNKNOWN (Switch On)" : "UNKNOWN (Switch Off)"
                return (status, "UNKNOWN")
            }

            if depth < 5 {
                if let res = findVpnStatus(element: child, depth: depth + 1) {
                    return res
                }
            }
        }
    }
    return nil
}

var statusResult = "{\"status\": \"UNKNOWN\", \"error\": \"VPN UI elements not found\"}"
if let _ = findVpnStatus(element: appElement) {
    statusResult = "{\"status\": \"UNKNOWN\", \"note\": \"UI found but state not fully parsed\"}"
}

print(statusResult)
