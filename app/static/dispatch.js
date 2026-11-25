const $ = (id) => document.getElementById(id);
const clock = (seconds) =>
  new Date(seconds * 1000)
    .toLocaleTimeString("zh-CN", { timeZone: "Asia/Shanghai", hour12: false })
    .slice(0, 5);
const statusNames = {
  PROMOTED: "已递补",
  WAITING: "排队中",
  REJECTED: "未受理",
  CLOSED: "已截止",
};
const eventNames = {
  hold: "保留",
  pay: "支付",
  wait: "候补",
  refund: "退票",
  swap: "换票",
};
let data,
  key = "dirty",
  requestNumber = 0,
  runId;
function tag(name, text, style) {
  const node = document.createElement(name);
  if (text !== undefined) node.textContent = text;
  if (style) node.className = style;
  return node;
}
async function get(path, options) {
  const reply = await fetch(path, options);
  const result = await reply.json();
  if (!reply.ok) throw Error(result.message || "读取失败，请重试");
  return result;
}
function table(headers, rows) {
  if (!rows.length) return tag("p", "暂无记录", "empty");
  const result = tag("table"),
    head = result.createTHead().insertRow();
  headers.forEach((value) => head.append(tag("th", value)));
  const body = result.createTBody();
  for (const entry of rows) {
    const row = body.insertRow();
    entry.forEach((value, i) =>
      row.append(tag("td", value, i === 0 ? "num" : "")),
    );
  }
  return result;
}
async function load(name) {
  const current = ++requestNumber;
  const save = $("archive-form").querySelector("button");
  save.disabled = true;
  $("balance").textContent = "正在清算";
  try {
    const parts = [
      "sailings",
      "seats",
      "orders",
      "transfers",
      "waitlist",
      "reconcile",
    ];
    const result = await Promise.all(
      parts.map((part) => get(`/api/${part}/${encodeURIComponent(name)}`)),
    );
    if (current !== requestNumber) return;
    key = name;
    data = Object.fromEntries(parts.map((part, i) => [part, result[i]]));
    $("shift").textContent = `清算时点 ${clock(data.sailings.as_of)}`;
    $("balance").textContent =
      data.reconcile.status === "MATCHED" ? "船班席位已对平" : "席位存在差异";
    $("trip").replaceChildren(
      new Option("全部船班", ""),
      ...Object.values(data.sailings.sailings)
        .sort((a, b) => a.departure - b.departure)
        .map((trip) => new Option(trip.destination, trip.id)),
    );
    $("archive-actions").hidden = true;
    $("archive-feedback").textContent = "";
    runId = undefined;
    draw();
    save.disabled = false;
  } catch (error) {
    if (current === requestNumber) $("balance").textContent = error.message;
  }
}
function draw() {
  const { reconcile, waitlist, sailings, seats } = data;
  const totals = reconcile.totals;
  $("totals").replaceChildren(
    ...[
      ["总容量", totals.capacity],
      ["出票", totals.issued],
      ["保留", totals.held],
      ["开放余位", totals.open],
      ["已递补", waitlist.counts.promoted],
    ].map(([title, value]) => {
      const card = tag("div", undefined, "kpi");
      card.append(tag("span", title), tag("b", value));
      return card;
    }),
  );
  $("routes").replaceChildren(
    ...Object.values(sailings.sailings)
      .sort((a, b) => a.departure - b.departure)
      .map((trip) => {
        const card = tag("article", undefined, "ticket");
        const heading = tag("header");
        const route = tag("div");
        route.append(
          tag("code", trip.id),
          tag("h3", `${trip.origin} → ${trip.destination}`),
        );
        const button = tag("button", `查看${trip.destination}`);
        button.onclick = () => {
          $("trip").value = trip.id;
          dispatch();
          $("dispatch").scrollIntoView({ block: "nearest" });
        };
        heading.append(route, button);
        card.append(
          heading,
          tag(
            "p",
            `${clock(trip.departure)} 发船　${trip.sailed ? "已发船" : trip.bookable ? "可办理" : "已截单"}　${clock(trip.refund_until)} 停退`,
          ),
        );
        reconcile.tiers
          .filter((row) => row.trip === trip.id)
          .forEach((row) => {
            const tier = tag("div", undefined, "tier");
            const groups = seats.tiers[row.trip][row.tier].groups.join("、");
            tier.append(
              tag("b", `${row.tier} · ${groups}`),
              tag("span", `出票 ${row.issued}`, "num"),
              tag("span", `保留 ${row.held}`, "num"),
              tag("span", `余位 ${row.open}`, "num"),
            );
            card.append(tier);
          });
        return card;
      }),
  );
  dispatch();
  evidence();
}
function dispatch() {
  if (!data) return;
  const trip = $("trip").value;
  const moves = data.transfers.moves.filter(
    (row) =>
      !trip ||
      row.requested_trip === trip ||
      row.target_trip === trip ||
      row.from?.trip === trip ||
      row.to?.trip === trip,
  );
  $("moves").replaceChildren(
    table(
      ["时间", "订单", "动作", "判定"],
      moves.map((row) => [
        clock(row.time),
        row.order,
        eventNames[row.action],
        row.code
          ? {
              NO_CAPACITY: "目标满席",
              STALE_TICKET: "原票失效",
              LATE_REFUND: "退票迟到",
              SELF_SWAP: "同席换票",
              NOT_ELIGIBLE: "资格不符",
              BOOKING_CLOSED: "已截单",
              UNKNOWN_SEAT: "席位不存在",
            }[row.code] || row.code
          : row.to
            ? `改签 → ${row.to.trip}`
            : "退票生效",
      ]),
    ),
  );
  const queue = data.waitlist.queue.filter((row) => !trip || row.trip === trip);
  $("queue").replaceChildren(
    table(
      ["排队时间", "订单", "席位", "状态", "出票时间"],
      queue.map((row) => [
        clock(row.queued_at),
        row.order,
        row.tier,
        statusNames[row.state],
        row.promoted_at ? clock(row.promoted_at) : "—",
      ]),
    ),
  );
}
function evidence() {
  if (!data) return;
  let headers, rows;
  const { orders, transfers, seats, sailings } = data;
  if ($("evidence-mode").value === "events") {
    headers = ["来源行", "订单", "动作", "回传时间"];
    rows = orders.events.map((row) => [
      row.row,
      row.order,
      eventNames[row.type],
      clock(row.received),
    ]);
  } else if ($("evidence-mode").value === "holds") {
    headers = ["来源行", "订单", "船班", "释放时间"];
    rows = transfers.expired_holds.map((row) => [
      row.row,
      row.order,
      row.trip,
      clock(row.released_at),
    ]);
  } else {
    headers = ["来源行", "单号 / 船班", "判定"];
    rows = [
      ...transfers.isolated,
      ...orders.duplicates,
      ...orders.isolated,
      ...seats.isolated,
      ...sailings.isolated,
    ].map((row) => [
      row.row,
      row.raw?.order || row.raw?.trip || row.raw?.id || "—",
      row.message,
    ]);
  }
  $("event-ledger").replaceChildren(table(headers, rows));
}
$("trip").onchange = dispatch;
$("evidence-mode").onchange = evidence;
$("sample").onchange = (e) => load(e.target.value);
$("import").onchange = async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  try {
    const result = await get("/api/sources", { method: "POST", body: file });
    $("sample").add(new Option(file.name, result.source, true, true));
    load(result.source);
  } catch (error) {
    $("balance").textContent = error.message;
  } finally {
    e.target.value = "";
  }
};
$("archive-form").onsubmit = async (e) => {
  e.preventDefault();
  const source = key;
  const button = e.submitter;
  button.disabled = true;
  try {
    const result = await get("/api/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source, operator: $("operator").value }),
    });
    if (source !== key) return;
    runId = result.id;
    $("archive-feedback").textContent = result.approval.decision;
    $("download").href = `/api/runs/${runId}/export`;
    $("archive-actions").hidden = false;
  } catch (error) {
    $("archive-feedback").textContent = error.message;
  } finally {
    button.disabled = false;
  }
};
$("rerun").onclick = async () => {
  try {
    const result = await get(`/api/runs/${runId}/rerun`, { method: "POST" });
    $("archive-feedback").textContent =
      `复跑一致 · ${result.manifest.digest.slice(0, 12)}`;
  } catch (error) {
    $("archive-feedback").textContent = error.message;
  }
};
load(key);
