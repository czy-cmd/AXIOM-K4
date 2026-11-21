/* AXIOM · Model K4 / Alpha 3 · 网页侧配置 */
window.K4_CONFIG = {
  product: "AXIOM",
  model: "K4",
  edition: "Alpha 3",
  remote_url: "",
  local_html: "index.html",
  network_message: "网络故障，尝试打开本地html中……",
  version: "K4-Alpha3",
  author: "CZY",
  debug_password: "devczy",
  store_key: "k4_alpha3_userdata_v1",
  time_limit: 300,
  agent_count: 12,
  difficulties: [
    { code: "minimal", label: "热身", min: 0.9, max: 1.3, desc: "只做最少的活" },
    { code: "low", label: "稳速", min: 1.5, max: 2.1, desc: "轻载运行" },
    { code: "medium", label: "基准", min: 2.3, max: 3.1, desc: "默认平衡点" },
    { code: "high", label: "高压", min: 3.4, max: 4.4, desc: "多线并行推进" },
    { code: "xhigh", label: "极限", min: 4.6, max: 6.2, desc: "全力推理，不留余量" }
  ]
};
