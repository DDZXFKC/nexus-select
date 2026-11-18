import Cocoa
import ApplicationServices

// 1. アクセシビリティ許可の確認
let isTrusted = AXIsProcessTrusted()
print("=== AX Trusted: \(isTrusted) ===\n")

if !isTrusted {
    print("アクセシビリティ権限がありません。システム設定 > プライバシーとセキュリティ > アクセシビリティで許可してください。")
    exit(1)
}

// 2. システム設定のVPNペインを開く
let url = URL(string: "x-apple.systempreferences:com.apple.preferences.network?VPN")!
NSWorkspace.shared.open(url)

// UI描画を待機
Thread.sleep(forTimeInterval: 3.0)

// システム設定アプリのAXUIElementを取得
guard let app = NSWorkspace.shared.runningApplications.first(where: { $0.bundleIdentifier == "com.apple.systempreferences" }) else {
    print("システム設定アプリが見つかりません。")
    exit(1)
}

let pid = app.processIdentifier
let appElement = AXUIElementCreateApplication(pid)

var elementCount = 0
let maxElements = 2000
let maxDepth = 12

var matchedElements: [String] = []
let keywords = ["AHC DE", "AHC US", "接続", "未接続", "Connected", "Not Connected"]

// 3. AXツリーを再帰的にダンプする関数
func dumpAXTree(element: AXUIElement, depth: Int, prefix: String) {
    if depth > maxDepth || elementCount >= maxElements {
        return
    }
    elementCount += 1

    // 属性値を取得
    var roleRef: CFTypeRef?
    var subroleRef: CFTypeRef?
    var titleRef: CFTypeRef?
    var valueRef: CFTypeRef?
    var descRef: CFTypeRef?
    var identifierRef: CFTypeRef?

    AXUIElementCopyAttributeValue(element, kAXRoleAttribute as CFString, &roleRef)
    AXUIElementCopyAttributeValue(element, kAXSubroleAttribute as CFString, &subroleRef)
    AXUIElementCopyAttributeValue(element, kAXTitleAttribute as CFString, &titleRef)
    AXUIElementCopyAttributeValue(element, kAXValueAttribute as CFString, &valueRef)
    AXUIElementCopyAttributeValue(element, kAXDescriptionAttribute as CFString, &descRef)
    AXUIElementCopyAttributeValue(element, kAXIdentifierAttribute as CFString, &identifierRef)

    let role = roleRef as? String ?? ""
    let subrole = subroleRef as? String ?? ""
    let title = titleRef as? String ?? ""
    let value = valueRef as? String ?? ""
    let desc = descRef as? String ?? ""
    let identifier = identifierRef as? String ?? ""

    // 値があるものだけ出力
    var line = "[D\(depth)] \(prefix)Role: \(role)"
    if !subrole.isEmpty { line += " | Sub: \(subrole)" }
    if !title.isEmpty { line += " | Title: \(title)" }
    if !value.isEmpty { line += " | Value: \(value)" }
    if !desc.isEmpty { line += " | Desc: \(desc)" }
    if !identifier.isEmpty { line += " | ID: \(identifier)" }

    print(line)

    // 該当キーワードを含む要素を抽出
    let combinedText = "\(title) \(value) \(desc)"
    for kw in keywords {
        if combinedText.contains(kw) {
            matchedElements.append("[D\(depth)] Role: \(role) | Title: \(title) | Value: \(value) | Desc: \(desc)")
            break
        }
    }

    // 子要素を再帰処理
    var childrenRef: CFArray?
    let result = AXUIElementCopyAttributeValues(element, kAXChildrenAttribute as CFString, 0, maxElements, &childrenRef)

    if result == .success, let children = childrenRef as? [AXUIElement] {
        for (index, child) in children.enumerated() {
            if elementCount >= maxElements { break }
            dumpAXTree(element: child, depth: depth + 1, prefix: "\(prefix)\(index).")
        }
    }
}

print("=== AX Tree Dump ===")
dumpAXTree(element: appElement, depth: 0, prefix: "")

print("\n=== Matched Keywords ===")
if matchedElements.isEmpty {
    print("該当キーワードを含む要素は見つかりませんでした。")
} else {
    for elem in matchedElements {
        print(elem)
    }
}
