function render({ model, el }) {
  el.innerHTML = "";
  const root = document.createElement("div");
  root.className = "ps-root";
  root.innerHTML = `
    <div class="ps-toolbar">
      <b data-title>调度台</b>
      <span data-algo></span>
      <span class="ps-hint">点击场地设起点 / 终点 / 障碍 · 右栏单步看搜索</span>
    </div>
    <div class="ps-floor"><canvas></canvas></div>
    <div class="ps-side">
      <div>
        <button data-act="step">单步</button>
        <button data-act="play">播放</button>
        <button data-act="reset">复位</button>
      </div>
      <div>速度 <input data-speed type="range" min="1" max="20" value="8" /></div>
      <div>eval <span class="ps-lamp idle" data-lamp>IDLE</span></div>
      <div class="ps-legend">
        <i class="ps-swatch" style="background:#1e293b"></i>空地
        <i class="ps-swatch" style="background:#0b1220"></i>墙
        <i class="ps-swatch" style="background:#4f46e5"></i>已扩展
        <i class="ps-swatch" style="background:#22d3ee"></i>待扩展
        <i class="ps-swatch" style="background:#facc15"></i>路径
        <i class="ps-swatch" style="background:#f472b6"></i>当前
        <i class="ps-swatch" style="background:#4ade80"></i>起点 S
        <i class="ps-swatch" style="background:#f43f5e"></i>终点 G
      </div>
      <div class="ps-metrics" data-metrics></div>
      <div class="ps-caption" data-caption></div>
      <div class="ps-tree" data-tree></div>
    </div>
    <div class="ps-timeline">
      <span>t</span>
      <input data-slider type="range" min="0" max="0" value="0" />
      <span data-t>0</span>
    </div>
  `;
  el.appendChild(root);
  const canvas = root.querySelector("canvas");
  const ctx = canvas.getContext("2d");
  const slider = root.querySelector("[data-slider]");
  const lamp = root.querySelector("[data-lamp]");
  const metricsEl = root.querySelector("[data-metrics]");
  const captionEl = root.querySelector("[data-caption]");
  const treeEl = root.querySelector("[data-tree]");
  const titleEl = root.querySelector("[data-title]");
  const algoEl = root.querySelector("[data-algo]");
  let playing = false;
  let timer = null;

  function sizeCanvas() {
    const floor = root.querySelector(".ps-floor");
    const r = floor.getBoundingClientRect();
    canvas.width = Math.max(200, r.width * devicePixelRatio);
    canvas.height = Math.max(200, r.height * devicePixelRatio);
    ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
  }

  function frames() {
    return model.get("frames") || [];
  }
  function fmap() {
    return model.get("map") || { kind: "grid", width: 8, height: 8, obstacles: [] };
  }
  function pal() {
    const s = getComputedStyle(root);
    const v = (name, fb) => s.getPropertyValue(name).trim() || fb;
    return {
      yard: v("--yard", "#020617"),
      cell: v("--cell", "#1e293b"),
      wall: v("--wall", "#0b1220"),
      closed: v("--closed", "#4f46e5"),
      open: v("--open", "#22d3ee"),
      path: v("--path", "#facc15"),
      current: v("--current", "#f472b6"),
      lock: v("--lock", "#f97316"),
      start: v("--start", "#4ade80"),
      goal: v("--goal", "#f43f5e"),
      a: v("--a", "#00d4ff"),
      b: v("--b", "#ff4d6d"),
      c: v("--c", "#b8ff3d"),
      d: v("--d", "#c77dff"),
      ink: v("--ink", "#f8fafc"),
      edge: v("--edge", "#fbbf24"),
      edgeBi: v("--edge-bi", "#38bdf8"),
      border: v("--border", "#334155"),
    };
  }
  function agentColor(i, p) {
    return [p.a, p.b, p.c, p.d][i % 4];
  }

  function draw() {
    const m = fmap();
    const fs = frames();
    const step = model.get("step") || 0;
    const fr = fs[Math.min(step, Math.max(0, fs.length - 1))] || {};
    const w = canvas.width / devicePixelRatio;
    const h = canvas.height / devicePixelRatio;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = pal().yard;
    ctx.fillRect(0, 0, w, h);
    if (m.kind === "grid") drawGrid(m, fr, w, h);
    else if (m.kind === "continuous") drawCont(m, fr, w, h);
    else drawTopo(m, fr, w, h);
    captionEl.textContent = fr.caption || "";
    const ev = model.get("eval") || {};
    lamp.className = "ps-lamp " + (ev.status === "pass" ? "pass" : ev.status === "fail" ? "fail" : "idle");
    lamp.textContent = (ev.status || "idle").toUpperCase();
    const met = model.get("metrics") || {};
    metricsEl.innerHTML = [
      ["成功", met.found === false ? "否" : met.found ? "是" : "—"],
      ["代价 / SOC", met.cost ?? "—"],
      ["扩展节点", met.expanded ?? "—"],
      ["高层节点", met.high ?? "—"],
      ["碰撞", met.conflicts ?? "—"],
      ["等待", met.waits ?? "—"],
      ["间隙", met.gap ?? "—"],
      ["用时 ms", met.ms ?? "—"],
    ]
      .map(([k, v]) => `${k}  <span>${v}</span>`)
      .join("<br/>");
    if (fr.tree) {
      treeEl.textContent = fr.tree;
    }
    algoEl.textContent = model.get("algo") || "";
    titleEl.textContent = model.get("title") || "调度台";
    slider.max = String(Math.max(0, fs.length - 1));
    slider.value = String(step);
    root.querySelector("[data-t]").textContent = String(step);
  }

  function drawGrid(m, fr, w, h) {
    const p = pal();
    const cols = m.width || 8;
    const rows = m.height || 8;
    const pad = 16;
    const cw = (w - pad * 2) / cols;
    const ch = (h - pad * 2) / rows;
    const obstacles = new Set((m.obstacles || []).map((pt) => pt.join(",")));
    const closed = new Set((fr.closed || []).map((n) => idkey(n)));
    const open = new Set((fr.open || []).map((n) => idkey(n)));
    const path = new Set((fr.path || []).map((n) => (Array.isArray(n) ? n.join(",") : n.id ? idkey(n) : n)));
    const locks = new Set((fr.locks || []).map((n) => (Array.isArray(n) ? n.join(",") : n)));
    const start = m.start && asxy(m.start);
    const goal = m.goal && asxy(m.goal);
    const sk = start ? `${start[0]},${start[1]}` : "";
    const gk = goal ? `${goal[0]},${goal[1]}` : "";
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        const X = pad + x * cw;
        const Y = pad + y * ch;
        const k = `${x},${y}`;
        let fill = obstacles.has(k) ? p.wall : p.cell;
        if (closed.has(k)) fill = p.closed;
        if (open.has(k)) fill = p.open;
        if (k === sk) fill = p.start;
        if (k === gk) fill = p.goal;
        if (path.has(k)) fill = p.path;
        if (locks.has(k)) fill = p.lock;
        ctx.fillStyle = fill;
        ctx.fillRect(X + 1, Y + 1, cw - 2, ch - 2);
        ctx.strokeStyle = obstacles.has(k) ? "#475569" : "rgba(148,163,184,0.28)";
        ctx.lineWidth = 1;
        ctx.strokeRect(X, Y, cw, ch);
      }
    }
    if (fr.current) {
      const c = asxy(fr.current);
      if (c) {
        ctx.strokeStyle = p.current;
        ctx.lineWidth = 3;
        ctx.strokeRect(pad + c[0] * cw + 2, pad + c[1] * ch + 2, cw - 4, ch - 4);
      }
    }
    (fr.agents || []).forEach((ag, i) => {
      const col = agentColor(i, p);
      const trail = ag.trail || [];
      if (trail.length > 1) {
        ctx.strokeStyle = col;
        ctx.lineWidth = 3;
        ctx.beginPath();
        trail.forEach((node, ti) => {
          const q = asxy(node);
          if (!q) return;
          const x = pad + (q[0] + 0.5) * cw;
          const y = pad + (q[1] + 0.5) * ch;
          if (ti === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        });
        ctx.stroke();
      }
      const pos = asxy(ag.pos);
      if (!pos) return;
      const ax = pad + (pos[0] + 0.5) * cw;
      const ay = pad + (pos[1] + 0.5) * ch;
      ctx.beginPath();
      ctx.arc(ax, ay, Math.min(cw, ch) * 0.3, 0, Math.PI * 2);
      ctx.fillStyle = col;
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = p.yard;
      ctx.stroke();
    });
    if (start) badge(pad + (start[0] + 0.5) * cw, pad + (start[1] + 0.5) * ch, p.start, "S");
    if (goal) badge(pad + (goal[0] + 0.5) * cw, pad + (goal[1] + 0.5) * ch, p.goal, "G");
  }

  function drawTopo(m, fr, w, h) {
    const p = pal();
    const nodes = m.nodes || [];
    if (!nodes.length) return;
    const xs = nodes.map((n) => n.x);
    const ys = nodes.map((n) => n.y);
    const minx = Math.min(...xs) - 0.6;
    const maxx = Math.max(...xs) + 0.6;
    const miny = Math.min(...ys) - 0.6;
    const maxy = Math.max(...ys) + 0.6;
    const pad = 28;
    const sx = (w - pad * 2) / (maxx - minx);
    const sy = (h - pad * 2) / (maxy - miny);
    const s = Math.min(sx, sy);
    const ox = pad + ((w - pad * 2) - (maxx - minx) * s) / 2;
    const oy = pad + ((h - pad * 2) - (maxy - miny) * s) / 2;
    const xy = (n) => [ox + (n.x - minx) * s, h - (oy + (n.y - miny) * s)];
    const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));
    ctx.lineWidth = 2.5;
    (m.edges || []).forEach((e) => {
      const a = byId[e.from];
      const b = byId[e.to];
      if (!a || !b) return;
      const [x1, y1] = xy(a);
      const [x2, y2] = xy(b);
      ctx.strokeStyle = e.bidir ? p.edgeBi : p.edge;
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
      if (!e.bidir) {
        const ang = Math.atan2(y2 - y1, x2 - x1);
        ctx.beginPath();
        ctx.moveTo(x2, y2);
        ctx.lineTo(x2 - 10 * Math.cos(ang - 0.4), y2 - 10 * Math.sin(ang - 0.4));
        ctx.lineTo(x2 - 10 * Math.cos(ang + 0.4), y2 - 10 * Math.sin(ang + 0.4));
        ctx.fillStyle = p.edge;
        ctx.fill();
      }
    });
    const pathset = new Set((fr.path || []).map((n) => (typeof n === "string" ? n : n.id || n)));
    const open = new Set((fr.open || []).map((n) => n.id || n));
    const closed = new Set((fr.closed || []).map((n) => n.id || n));
    nodes.forEach((n) => {
      const [x, y] = xy(n);
      ctx.beginPath();
      ctx.arc(x, y, 12, 0, Math.PI * 2);
      let fill = n.no_pass ? "#7f1d1d" : p.cell;
      if (closed.has(n.id)) fill = p.closed;
      if (open.has(n.id)) fill = p.open;
      if (pathset.has(n.id)) fill = p.path;
      ctx.fillStyle = fill;
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = n.kind === "intersection" ? p.edge : p.border;
      ctx.stroke();
      ctx.fillStyle = pathset.has(n.id) || open.has(n.id) ? p.yard : p.ink;
      ctx.font = "11px IBM Plex Mono";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(n.id, x, y);
    });
    (fr.agents || []).forEach((ag, i) => {
      const n = byId[ag.pos];
      if (!n) return;
      const [x, y] = xy(n);
      ctx.fillStyle = agentColor(i, p);
      ctx.beginPath();
      ctx.arc(x, y - 20, 7, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = p.yard;
      ctx.lineWidth = 2;
      ctx.stroke();
    });
  }

  function drawCont(m, fr, w, h) {
    const p = pal();
    const pad = 16;
    const sx = (w - pad * 2) / (m.width || 1);
    const sy = (h - pad * 2) / (m.height || 1);
    (m.obstacles || []).forEach((ob) => {
      ctx.beginPath();
      ctx.arc(pad + ob.x * sx, pad + ob.y * sy, ob.r * sx, 0, Math.PI * 2);
      ctx.fillStyle = "#111827";
      ctx.fill();
      ctx.strokeStyle = "#f43f5e";
      ctx.lineWidth = 2;
      ctx.stroke();
    });
    const nodes = fr.rrt_nodes || [];
    const parent = fr.rrt_parent || [];
    ctx.strokeStyle = "rgba(34,211,238,0.55)";
    ctx.lineWidth = 1.25;
    nodes.forEach((pt, i) => {
      const par = parent[i];
      if (par == null) return;
      const q = nodes[par];
      ctx.beginPath();
      ctx.moveTo(pad + q[0] * sx, pad + q[1] * sy);
      ctx.lineTo(pad + pt[0] * sx, pad + pt[1] * sy);
      ctx.stroke();
    });
    const path = fr.path || [];
    if (path.length) {
      ctx.strokeStyle = p.path;
      ctx.lineWidth = 3;
      ctx.beginPath();
      path.forEach((pt, i) => {
        const x = pad + pt[0] * sx;
        const y = pad + pt[1] * sy;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
    }
    if (m.start) badge(pad + m.start[0] * sx, pad + m.start[1] * sy, p.start, "S");
    if (m.goal) badge(pad + m.goal[0] * sx, pad + m.goal[1] * sy, p.goal, "G");
  }

  function badge(x, y, color, label) {
    ctx.beginPath();
    ctx.arc(x, y, 9, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = pal().yard;
    ctx.stroke();
    ctx.fillStyle = pal().yard;
    ctx.font = "bold 11px IBM Plex Mono";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(label, x, y);
  }
  function idkey(n) {
    if (Array.isArray(n)) return n.join(",");
    if (n && n.id) return Array.isArray(n.id) ? n.id.join(",") : String(n.id);
    return String(n);
  }
  function asxy(n) {
    if (Array.isArray(n)) return n;
    if (n && Array.isArray(n.id)) return n.id;
    if (typeof n === "string" && n.includes(",")) return n.split(",").map(Number);
    return null;
  }

  canvas.addEventListener("click", (ev) => {
    const rect = canvas.getBoundingClientRect();
    const x = ev.clientX - rect.left;
    const y = ev.clientY - rect.top;
    const m = fmap();
    if (m.kind === "grid") {
      const pad = 16;
      const cw = (rect.width - pad * 2) / m.width;
      const ch = (rect.height - pad * 2) / m.height;
      const gx = Math.floor((x - pad) / cw);
      const gy = Math.floor((y - pad) / ch);
      model.set("click", { kind: "cell", x: gx, y: gy, t: Date.now() });
      model.save_changes();
    }
  });

  root.querySelector("[data-act=step]").onclick = () => {
    playing = false;
    model.set("step", Math.min((model.get("step") || 0) + 1, Math.max(0, frames().length - 1)));
    model.save_changes();
  };
  root.querySelector("[data-act=play]").onclick = () => {
    playing = !playing;
    root.querySelector("[data-act=play]").textContent = playing ? "暂停" : "播放";
  };
  root.querySelector("[data-act=reset]").onclick = () => {
    playing = false;
    model.set("step", 0);
    model.save_changes();
  };
  slider.oninput = () => {
    model.set("step", Number(slider.value));
    model.save_changes();
  };

  function tick() {
    if (playing) {
      const fs = frames();
      const s = model.get("step") || 0;
      if (s < fs.length - 1) {
        model.set("step", s + 1);
        model.save_changes();
      } else playing = false;
    }
    draw();
    requestAnimationFrame(tick);
  }
  window.addEventListener("resize", () => {
    sizeCanvas();
    draw();
  });
  model.on("change:frames", draw);
  model.on("change:step", draw);
  model.on("change:map", draw);
  model.on("change:metrics", draw);
  model.on("change:eval", draw);
  sizeCanvas();
  requestAnimationFrame(tick);
}

export default { render };
