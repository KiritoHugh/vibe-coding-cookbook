document.addEventListener('DOMContentLoaded', function () {
  const stitchButton = document.getElementById('stitchImages');

  if (stitchButton) {
    stitchButton.addEventListener('click', function () {
      chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
        if (tabs[0] && tabs[0].id) {
          chrome.scripting.executeScript({
            target: { tabId: tabs[0].id },
            // files: ['content.js'] // 移除此行
            function: stitchImagesProcess // 直接执行函数
          }, (injectionResults) => {
            if (chrome.runtime.lastError) {
              console.error('Error executing content script function: ', chrome.runtime.lastError.message);
              return;
            }
            // 检查 injectionResults，如果需要，可以从这里获取函数返回的状态
            if (injectionResults && injectionResults[0] && injectionResults[0].result) {
              console.log(injectionResults[0].result);
            } else {
              console.log("Function executed, but no explicit result returned or unexpected format.");
            }
          });
        } else {
          console.error("Could not get active tab ID.");
        }
      });
    });
  } else {
    console.error("Button with ID 'stitchImages' not found.");
  }
});

// 将 stitchImagesProcess 函数从 content.js 复制到这里，或者确保它在 popup.js 可访问的范围内
// 注意：为了让 chrome.scripting.executeScript 的 function 参数工作，
// stitchImagesProcess 必须是一个独立的、不依赖于 content.js 中其他未导出变量的函数。
// 最佳实践是将其定义在 popup.js 中，或者从一个共享模块导入。
// 为了简化，我将 stitchImagesProcess 的内容直接放在这里，但请注意这会使 popup.js 变得很大。
// 更好的方法是将其放在一个单独的文件中，并通过 chrome.scripting.executeScript 的 files 属性加载。
// 但由于您的问题是重复执行，直接执行函数是更直接的解决方案。

async function stitchImagesProcess() {
  // 1. Find image URLs
  const imageElements = Array.from(document.querySelectorAll('.swiper-slide img'));

  let imageUrls = imageElements
    .map(img => img.src)
    .filter(src => src && (src.startsWith('http://') || src.startsWith('https://')))
    .filter(src => src.includes('xhscdn.com')); // Filter for Xiaohongshu CDN images

  imageUrls = [...new Set(imageUrls)];

  console.log("Found image URLs:", imageUrls);
  // 如果 imageUrls 非空，第一个移到最后
  if (imageUrls.length > 0) {
    const firstUrl = imageUrls.shift();
    imageUrls.push(firstUrl);
  }

  if (imageUrls.length === 0) {
    const allImages = Array.from(document.getElementsByTagName('img'));
    imageUrls = allImages
      .map(img => img.src)
      .filter(src => src && src.includes('xhscdn.com') && (src.includes('/photo/') || src.includes('/discovery/')))
      .filter(src => !src.includes('avatar'))
      .map(src => src.split('?')[0]);
    imageUrls = [...new Set(imageUrls)];
    console.log("Found image URLs (general approach):\从小红书图片拼接助手 content script loaded。", imageUrls);

    if (imageUrls.length === 0) {
      return "未找到图片。请确保在小红书帖子页面。选择器可能需要更新。";
    }
  }

  // 2. Fetch and load images
  const loadedImages = [];
  for (const url of imageUrls) {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        console.warn(`Failed to fetch ${url}: ${response.statusText}`);
        continue;
      }
      const blob = await response.blob();
      const image = await new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = (err) => {
          console.error(`Error loading image ${url}:`, err);
          reject(new Error(`Failed to load image: ${url}`));
        };
        img.src = URL.createObjectURL(blob);
      });
      loadedImages.push(image);
    } catch (error) {
      console.warn(`Error processing image ${url}:`, error);
    }
  }

  if (loadedImages.length === 0) {
    return "无法加载任何图片。";
  }

  console.log("Loaded images:", loadedImages.length);

  // create a new image from text, the text is from const descElement = document.querySelector('.note-scroller .desc');
// ===== 取 DOM 文本 =====
const titleElement = document.querySelector('.note-scroller .title');
const descElement = document.querySelector('.note-scroller .desc');
const usernameElement = document.querySelector('.author-wrapper .username');

const titleText = titleElement?.textContent.trim() || '';
const descText  = descElement?.textContent.trim()  || '';
const usernameText = usernameElement?.textContent.trim() ? `@${usernameElement.textContent.trim()}` : '';

// 如果至少有 title 或 desc，就生成图片
if (titleText || descText) {
  // ---------- 1) 先做测量 ----------
  const measureCanvas = document.createElement('canvas');
  measureCanvas.width = 800;        // 最终宽度就按 800 来
  const mCtx = measureCanvas.getContext('2d');

  const maxWidth   = measureCanvas.width * 0.8; // 左右各留 10%
  const lineHeight = 40;

  // 拆行函数：根据当前 mCtx.font 来测宽
  function wrapText(ctx, text) {
    const words = text.split('');        // 按字符拆
    let lines = [], current = '';
    for (const ch of words) {
      const testLine = current + ch;
      if (ctx.measureText(testLine).width > maxWidth && current) {
        lines.push(current);
        current = ch;
      } else {
        current = testLine;
      }
    }
    if (current) lines.push(current);
    return lines;
  }

  // 依次换 font 测量
  mCtx.font = '36px Arial';
  const titleLines = wrapText(mCtx, titleText);

  mCtx.font = '24px Arial';
  const usernameLines = wrapText(mCtx, usernameText);

  mCtx.font = '30px Arial';
  const descLines = wrapText(mCtx, descText);

  // 行距配置
  const EMPTY_BEFORE           = 4; // 开头空行
  const EMPTY_BETWEEN_TITLE_U  = 1; // title ↔ username
  const EMPTY_BETWEEN_U_DESC   = 1; // username ↔ desc
  const EMPTY_BOTTOM           = 2; // 结尾额外空行，纯美观

  const totalLines =
    EMPTY_BEFORE +
    titleLines.length +
    EMPTY_BETWEEN_TITLE_U +
    usernameLines.length +
    EMPTY_BETWEEN_U_DESC +
    descLines.length +
    EMPTY_BOTTOM;

  const canvasHeight = totalLines * lineHeight;

  // ---------- 2) 再正式创建绘图 Canvas ----------
  const canvas = document.createElement('canvas');
  canvas.width  = measureCanvas.width;
  canvas.height = canvasHeight;
  const ctx = canvas.getContext('2d');

  // ---------- 3) 背景 ----------
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';

  let y = lineHeight * EMPTY_BEFORE;   // 从空行后开始

  // ---------- 4) 画 title ----------
  ctx.font = '36px Arial';
  ctx.fillStyle = '#000';
  titleLines.forEach(line => {
    ctx.fillText(line, canvas.width / 2, y);
    y += lineHeight;
  });

  y += lineHeight * EMPTY_BETWEEN_TITLE_U;

  // ---------- 5) 画 username ----------
  ctx.font = '24px Arial';
  ctx.fillStyle = '#888';
  usernameLines.forEach(line => {
    ctx.fillText(line, canvas.width / 2, y);
    y += lineHeight;
  });

  y += lineHeight * EMPTY_BETWEEN_U_DESC;

  // ---------- 6) 画 desc ----------
  ctx.font = '30px Arial';
  ctx.fillStyle = '#000';
  descLines.forEach(line => {
    ctx.fillText(line, canvas.width / 2, y);
    y += lineHeight;
  });

  // ---------- 7) 输出 ----------
  const dataURL = canvas.toDataURL('image/png');
  const textImage = await new Promise((resolve, reject) => {
    const img = new Image();
    img.onload  = () => resolve(img);
    img.onerror = reject;
    img.src = dataURL;
  });

  loadedImages.unshift(textImage);
}

  
  
  
  

  // log length of loadedImages
  console.log("Loaded images length:", loadedImages.length);

  // 3. Stitch images onto a canvas
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');

  let totalHeight = 0;
  let maxWidth = 0;
  loadedImages.forEach(img => {
    totalHeight += img.naturalHeight;
    if (img.naturalWidth > maxWidth) {
      maxWidth = img.naturalWidth;
    }
  });

  if (maxWidth === 0 || totalHeight === 0) {
    return "加载的图片尺寸无效。";
  }

  canvas.width = maxWidth;
  canvas.height = totalHeight;

  let currentY = 0;
  loadedImages.forEach(img => {
    ctx.drawImage(img, 0, currentY, img.naturalWidth, img.naturalHeight);
    currentY += img.naturalHeight;
    URL.revokeObjectURL(img.src);
  });

  console.log("Images stitched on canvas");

  // 4. Trigger download
  const dataUrl = canvas.toDataURL('image/png');
  const link = document.createElement('a');
  link.href = dataUrl;

  let postTitle = "xiaohongshu-stitched-images";
  try {
    // const titleElement = document.querySelector('.note-scroller .title');
    // const descElement = document.querySelector('.note-scroller .desc');
    if (titleElement && titleElement.textContent.trim()) {
      postTitle = titleElement.textContent.trim().replace(/[^a-zA-Z0-9\u4e00-\u9fa5_\-]+/g, '_');
    }
  } catch (e) {
    console.warn("Could not get post title:", e);
  }
  link.download = `${postTitle}.png`;

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  console.log("Download triggered");
  return "图片拼接完成并已开始下载！";
}