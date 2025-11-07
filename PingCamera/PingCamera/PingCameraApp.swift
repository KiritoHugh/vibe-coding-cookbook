//
//  PingCameraApp.swift
//  PingCamera
//
//  Created by Qiqi Zhou on 8/11/2025.
//

import SwiftUI

@main
struct PingCameraApp: App {
    @AppStorage("showTitleBar") private var showTitleBar: Bool = false
    
    var body: some Scene {
        WindowGroup {
            ContentView(showTitleBar: $showTitleBar)
        }
        .windowStyle(.hiddenTitleBar)
        
        MenuBarExtra("PingCamera", systemImage: "video.fill") {
            MenuBarContent(showTitleBar: $showTitleBar)
        }
    }
}

private struct MenuBarContent: View {
    @Binding var showTitleBar: Bool
    
    var body: some View {
        VStack {
            Toggle(isOn: $showTitleBar) {
                Text(showTitleBar ? "隐藏标题栏" : "显示标题栏")
            }
            .toggleStyle(.checkbox)
            
            Divider()
            
            Button("退出 PingCamera") {
                NSApplication.shared.terminate(nil)
            }
        }
        .padding(8)
    }
}
