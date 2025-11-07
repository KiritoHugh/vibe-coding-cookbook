//
//  CameraPreviewView.swift
//  PingCamera
//
//  Created by Codex on 8/11/2025.
//

import AppKit
import AVFoundation
import SwiftUI

struct CameraPreviewView: NSViewRepresentable {
    let session: AVCaptureSession

    func makeNSView(context: Context) -> PreviewHostingView {
        let view = PreviewHostingView()
        view.videoPreviewLayer.session = session
        return view
    }

    func updateNSView(_ nsView: PreviewHostingView, context: Context) {
        nsView.videoPreviewLayer.session = session
    }
}

final class PreviewHostingView: NSView {
    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        wantsLayer = true
        let previewLayer = AVCaptureVideoPreviewLayer()
        previewLayer.videoGravity = .resizeAspectFill
        layer = previewLayer
    }

    required init?(coder: NSCoder) {
        nil
    }

    var videoPreviewLayer: AVCaptureVideoPreviewLayer {
        guard let previewLayer = layer as? AVCaptureVideoPreviewLayer else {
            let newLayer = AVCaptureVideoPreviewLayer()
            newLayer.videoGravity = .resizeAspectFill
            layer = newLayer
            return newLayer
        }
        return previewLayer
    }

    override func layout() {
        super.layout()
        CATransaction.begin()
        CATransaction.setDisableActions(true)
        layer?.frame = bounds
        CATransaction.commit()
    }
}
