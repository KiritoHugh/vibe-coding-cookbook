#!/bin/bash
set -e

echo "🚀 开始构建 PingCamera Release 版本..."

# 项目路径
PROJECT_DIR="/Users/qiqizhou/Downloads/PingCamera"
SCHEME="PingCamera"
WORKSPACE_OR_PROJECT="PingCamera.xcodeproj"

# 输出路径
BUILD_DIR="$PROJECT_DIR/build"
ARCHIVE_PATH="$BUILD_DIR/PingCamera.xcarchive"
EXPORT_PATH="$BUILD_DIR/Export"

# 进入项目目录
cd "$PROJECT_DIR"

# 清理之前的构建
echo "🧹 清理之前的构建..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# 构建 Archive
echo "📦 创建 Archive..."
xcodebuild \
    -project "$WORKSPACE_OR_PROJECT" \
    -scheme "$SCHEME" \
    -configuration Release \
    -archivePath "$ARCHIVE_PATH" \
    archive \
    CODE_SIGN_IDENTITY="" \
    CODE_SIGNING_REQUIRED=NO \
    CODE_SIGNING_ALLOWED=NO

# 创建导出选项 plist
echo "📝 创建导出配置..."
cat > "$BUILD_DIR/ExportOptions.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>mac-application</string>
    <key>destination</key>
    <string>export</string>
    <key>signingStyle</key>
    <string>automatic</string>
    <key>stripSwiftSymbols</key>
    <true/>
    <key>teamID</key>
    <string></string>
</dict>
</plist>
EOF

# 导出应用
echo "📤 导出应用..."
xcodebuild \
    -exportArchive \
    -archivePath "$ARCHIVE_PATH" \
    -exportOptionsPlist "$BUILD_DIR/ExportOptions.plist" \
    -exportPath "$EXPORT_PATH" \
    -allowProvisioningUpdates

# 检查导出的应用
if [ -d "$EXPORT_PATH/PingCamera.app" ]; then
    echo "✅ 应用构建成功！"
    echo "📍 应用位置: $EXPORT_PATH/PingCamera.app"
    
    # 询问是否要复制到 Applications 文件夹
    echo ""
    echo "是否要将应用复制到 Applications 文件夹? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "📋 复制到 Applications 文件夹..."
        sudo cp -R "$EXPORT_PATH/PingCamera.app" /Applications/
        echo "✅ PingCamera 已安装到 Applications 文件夹"
        echo "🎉 现在可以在 Launchpad 或 Applications 文件夹中找到 PingCamera"
    else
        echo "💡 您可以手动将 $EXPORT_PATH/PingCamera.app 拖到 Applications 文件夹"
    fi
    
    # 显示应用信息
    echo ""
    echo "📊 应用信息:"
    ls -la "$EXPORT_PATH/PingCamera.app"
    
else
    echo "❌ 应用导出失败"
    echo "📋 检查导出目录:"
    ls -la "$EXPORT_PATH/"
    exit 1
fi

echo ""
echo "🎯 构建完成！"