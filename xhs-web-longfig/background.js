// 监听扩展安装或更新事件
chrome.runtime.onInstalled.addListener(() => {
  console.log('小红书图片拼接助手已安装/更新');
});

// 监听来自content script的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'error') {
    console.error('Content script error:', request.error);
  }
  return true;
});