const canvas = document.querySelector('#heatmap');
const context = canvas.getContext('2d');
const status = document.querySelector('#status');
const statusText = document.querySelector('#status-text');
const empty = document.querySelector('#empty');
let currentFrame = null;
let selected = null;

const stops = [
  [10, 20, 57], [26, 45, 115], [45, 104, 176], [41, 166, 167],
  [135, 205, 112], [246, 202, 71], [241, 109, 55], [200, 48, 76]
];

function colorAt(t) {
  const scaled = Math.max(0, Math.min(0.999, t)) * (stops.length - 1);
  const i = Math.floor(scaled);
  const f = scaled - i;
  return stops[i].map((v, channel) => Math.round(v + (stops[i + 1][channel] - v) * f));
}

function draw(frame) {
  const { pixels, width, height } = frame;
  const low = frame.minimum - 1;
  const high = Math.max(frame.maximum + 1, low + 2);
  const image = context.createImageData(canvas.width, canvas.height);
  for (let y = 0; y < canvas.height; y++) {
    for (let x = 0; x < canvas.width; x++) {
      const sensorX = Math.min(width - 1, Math.floor(x * width / canvas.width));
      const sensorY = Math.min(height - 1, Math.floor(y * height / canvas.height));
      const value = pixels[sensorY * width + sensorX];
      const color = colorAt((value - low) / (high - low));
      const offset = (y * canvas.width + x) * 4;
      image.data.set([...color, 255], offset);
    }
  }
  context.putImageData(image, 0, 0);
  if (selected) {
    const cellWidth = canvas.width / width;
    const cellHeight = canvas.height / height;
    context.strokeStyle = '#ffffff';
    context.lineWidth = 2;
    context.strokeRect(selected.x * cellWidth + 1, selected.y * cellHeight + 1, cellWidth - 2, cellHeight - 2);
  }
  document.querySelector('#scale-min').textContent = `${low.toFixed(1)} °C`;
  document.querySelector('#scale-max').textContent = `${high.toFixed(1)} °C`;
  if (selected) {
    const value = pixels[selected.y * width + selected.x];
    document.querySelector('#point').textContent = `選択位置 (${selected.x + 1}, ${selected.y + 1}): ${value.toFixed(1)} °C`;
  }
}

function setStatus(kind, label, message) {
  status.className = `status ${kind}`;
  statusText.textContent = label;
  document.querySelector('#message').textContent = message;
}

async function poll() {
  try {
    const response = await fetch('/api/frame', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const frame = await response.json();
    if (frame.status === 'live' && Array.isArray(frame.pixels)) {
      currentFrame = frame;
      empty.hidden = true;
      draw(frame);
      for (const key of ['maximum', 'minimum', 'average', 'ambient']) {
        document.getElementById(key).textContent = frame[key].toFixed(1);
      }
      document.querySelector('#updated').textContent = new Date(frame.captured_at).toLocaleTimeString('ja-JP');
      setStatus('live', 'ライブ', 'センサーから取得中');
    } else {
      setStatus('offline', frame.status === 'stale' ? '更新停止' : '再接続中', frame.error || 'センサーからの応答を待っています');
    }
  } catch (error) {
    setStatus('offline', '接続できません', 'サーバーとの通信を確認してください');
  } finally {
    window.setTimeout(poll, 700);
  }
}

canvas.addEventListener('pointerdown', event => {
  if (!currentFrame) return;
  const rect = canvas.getBoundingClientRect();
  selected = {
    x: Math.min(currentFrame.width - 1, Math.floor((event.clientX - rect.left) / rect.width * currentFrame.width)),
    y: Math.min(currentFrame.height - 1, Math.floor((event.clientY - rect.top) / rect.height * currentFrame.height))
  };
  draw(currentFrame);
});

poll();
