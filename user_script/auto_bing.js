// ==UserScript==
// @name         Microsoft Bing Rewards Helper (Full-Stack Edition)
// @version      2.2.0
// @description  自动完成 Bing 搜索任务，支持进度条展示及完整的控制逻辑。
// @author       Full-Stack Engineer
// @match        https://cn.bing.com/search?*
// @match        https://www.bing.com/search?*
// @grant        GM_setValue
// @grant        GM_getValue
// @require      https://code.jquery.com/jquery-3.1.1.min.js
// ==/UserScript==

(function() {
    'use strict';

    // --- 1. 状态与设置管理 (State & Settings Management) ---
    class RewardManager {
        constructor() {
            const today = new Date().toISOString().split("T")[0];
            this.settings = JSON.parse(GM_getValue("bing_settings", JSON.stringify({
                max_pc: 30,
                max_ph: 20,
            })));

            const storedProgress = JSON.parse(GM_getValue("bing_progress", "{}"));
            if (storedProgress.date !== today) {
                this.progress = { date: today, pc_count: 0, ph_count: 0 };
            } else {
                this.progress = storedProgress;
            }
        }

        saveSettings(newSettings) {
            this.settings = { ...this.settings, ...newSettings };
            GM_setValue("bing_settings", JSON.stringify(this.settings));
        }

        saveProgress() {
            GM_setValue("bing_progress", JSON.stringify(this.progress));
        }

        increment(isMobile) {
            if (isMobile) this.progress.ph_count++;
            else this.progress.pc_count++;
            this.saveProgress();
        }

        isAllDone() {
            return this.progress.pc_count >= this.settings.max_pc ||
                this.progress.ph_count >= this.settings.max_ph;
        }
    }

    const mgr = new RewardManager();
    let isPaused = false;
    let rewardInterval = null;
    let isRunning = false;

    // --- 2. 路由拦截器 (Navigation Interceptor) ---
    const interceptNavigation = (callback) => {
        const originalPushState = history.pushState;
        history.pushState = function() {
            originalPushState.apply(this, arguments);
            callback();
        };
        window.addEventListener('popstate', callback);
    };

    // --- 3. UI 界面 (Enhanced UI with Progress Bars) ---
    class RewardUI {
        constructor() {
            if (document.getElementById('bing-reward-helper-host')) return;
            this.host = document.createElement('div');
            this.host.id = 'bing-reward-helper-host';
            document.documentElement.appendChild(this.host);
            this.shadow = this.host.attachShadow({ mode: 'open' });
            this.render();
        }

        render() {
            const pcRatio = Math.min(100, (mgr.progress.pc_count / mgr.settings.max_pc) * 100);
            const phRatio = Math.min(100, (mgr.progress.ph_count / mgr.settings.max_ph) * 100);

            this.shadow.innerHTML = `
            <style>
                :host { position: fixed; right: 20px; bottom: 20px; z-index: 999999; }
                .panel {
                    background: #ffffff; border-radius: 16px; padding: 20px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.15); width: 260px;
                    font-family: 'Segoe UI', system-ui, sans-serif; border: 1px solid #eee;
                }
                .title { font-weight: 800; color: #0078d4; margin-bottom: 12px; font-size: 16px; border-bottom: 1px solid #f0f0f0; padding-bottom: 8px; }
                .row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; font-size: 13px; }

                .progress-section { background: #f8faff; padding: 12px; border-radius: 10px; margin: 12px 0; border: 1px solid #eef2ff; }
                .bar-label { font-size: 11px; color: #555; margin-bottom: 5px; display: flex; justify-content: space-between; }
                .bar-bg { background: #e0e6ed; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 10px; }
                .bar-fill { background: linear-gradient(90deg, #0078d4, #00bcf2); height: 100%; transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1); }

                input[type="number"] { width: 45px; padding: 4px; border: 1px solid #cbd5e0; border-radius: 6px; text-align: center; }

                .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px; }
                button { padding: 10px; cursor: pointer; border-radius: 8px; border: none; font-size: 12px; font-weight: 700; transition: all 0.2s; }
                button:active { transform: scale(0.95); }

                #save-btn { background: #0078d4; color: white; grid-column: span 2; box-shadow: 0 4px 12px rgba(0,120,212,0.3); }
                #pause-btn { background: #ffaa00; color: white; }
                #reset-btn { background: #f1f3f5; color: #495057; }

                .status-line { font-size: 13px; font-weight: bold; color: #d83b01; text-align: center; margin-top: 5px; }
            </style>
            <div class="panel">
                <div class="title">Bing Rewards Helper</div>
                <div class="row">
                    <span>PC Target:</span> <input type="number" id="in-pc" value="${mgr.settings.max_pc}">
                </div>
                <div class="row">
                    <span>PH Target:</span> <input type="number" id="in-ph" value="${mgr.settings.max_ph}">
                </div>

                <div class="progress-section">
                    <div class="bar-label"><span>Desktop</span> <span>${mgr.progress.pc_count}/${mgr.settings.max_pc}</span></div>
                    <div class="bar-bg"><div class="bar-fill" style="width: ${pcRatio}%"></div></div>
                    <div class="bar-label"><span>Mobile</span> <span>${mgr.progress.ph_count}/${mgr.settings.max_ph}</span></div>
                    <div class="bar-bg"><div class="bar-fill" style="width: ${phRatio}%"></div></div>
                </div>

                <div class="status-line">Status: <span id="status-text">Initializing...</span></div>

                <div class="btn-group">
                    <button id="save-btn">Start & Save Config</button>
                    <button id="pause-btn">Pause</button>
                    <button id="reset-btn">Reset Today</button>
                </div>
            </div>
            `;

            this.initEvents();
        }

        initEvents() {
            this.shadow.getElementById('save-btn').onclick = () => {
                const max_pc = parseInt(this.shadow.getElementById('in-pc').value);
                const max_ph = parseInt(this.shadow.getElementById('in-ph').value);
                mgr.saveSettings({ max_pc, max_ph });
                location.reload();
            };

            this.shadow.getElementById('pause-btn').onclick = (e) => {
                isPaused = !isPaused;
                e.target.textContent = isPaused ? "Resume" : "Pause";
                e.target.style.background = isPaused ? "#00b294" : "#ffaa00";
                this.updateStatus(isPaused ? "PAUSED" : "RUNNING");
            };

            this.shadow.getElementById('reset-btn').onclick = () => {
                if(confirm("Reset all progress for today?")) {
                    GM_setValue("bing_progress", "{}");
                    location.reload();
                }
            };
        }
        // --- RewardUI 类内部修改 ---
        updateProgress() {
            const pcRatio = Math.min(100, (mgr.progress.pc_count / mgr.settings.max_pc) * 100);
            const phRatio = Math.min(100, (mgr.progress.ph_count / mgr.settings.max_ph) * 100);

            // 重新更新进度条的宽度和文本 (Update bar width and text)
            const pcBar = this.shadow.querySelectorAll('.bar-fill')[0];
            const phBar = this.shadow.querySelectorAll('.bar-fill')[1];
            const labels = this.shadow.querySelectorAll('.bar-label span:last-child');

            if (pcBar) pcBar.style.width = `${pcRatio}%`;
            if (phBar) phBar.style.width = `${phRatio}%`;
            if (labels[0]) labels[0].textContent = `${mgr.progress.pc_count}/${mgr.settings.max_pc}`;
            if (labels[1]) labels[1].textContent = `${mgr.progress.ph_count}/${mgr.settings.max_ph}`;
        }
        updateStatus(msg) {
            const el = this.shadow.getElementById('status-text');
            if (el) el.textContent = msg;
            this.updateProgress(); // 强制刷新进度显示
        }
    }

    // --- 改进后的词库管理 (Improved Dictionary Management) ---
    function getUniqueTerm(index) {
        const baseTerms = [
            'DeepSeek开源模型', '大模型推理优化', '鸿蒙系统进展', '量子计算突破', '自动驾驶标准',
            '冬奥会场馆', '半导体产业', '碳中和路线', '商业航天计划', '数字经济政策',
            'CityWalk路线', '深度睡眠技巧', '高蛋白餐谱', '极简生活方式', '摄影入门教程',
            '自律给我自由', '如何学习Python', '全栈工程师技能', '数据结构面试题', '云原生架构',
            '人工智能伦理', '虚拟现实应用', '区块链技术底层', '低碳出行生活', '心理健康疏导',
            '英语口语练习', '理财投资入门', '经典电影推荐', '中国传统文化', '世界遗产名录',
            '宇宙黑洞奥秘', '深海探索发现', '生物基因工程', '绿色建筑设计', '智能家居体验',
            '网络安全防护', '分布式系统原理', '微服务架构实践', '容器化技术Docker', 'K8s部署指南',
            '前端框架对比', '后端语言性能', '数据库调优技巧', '消息队列选型', '机器学习算法',
            '神经网络可视化', '增强现实前景', '元宇宙核心概念', '边缘计算应用', '5G通信技术'
        ];

        // 使用 Seeded Shuffle 思想：虽然是随机打乱，但只要数组够大，按索引取值就能保证 50 次不重
        // 实际操作中，我们直接返回索引对应的词条
        const term = baseTerms[index % baseTerms.length];
        const suffix = ['最新', '教程', '评价', '趋势', '分析', new Date().getFullYear() + '年'];
        const randomSuffix = suffix[Math.floor(Math.random() * suffix.length)];

        return `${term} ${randomSuffix}`;
    }

    async function performSearch() {
        const isMobile = /Android|iPhone|iPad/i.test(navigator.userAgent) || window.innerWidth < 768;
        if ((isMobile && mgr.progress.ph_count >= mgr.settings.max_ph) ||
            (!isMobile && mgr.progress.pc_count >= mgr.settings.max_pc)) return;
        const currentIndex = isMobile ? mgr.progress.ph_count : mgr.progress.pc_count;
        const searchTerm = getUniqueTerm(currentIndex);
        const input = document.querySelector("#sb_form_q, input[name='q']");
        const btn = document.querySelector("#sb_form_go, button[type='submit']");

        if (input && btn) {
            input.value = "";
            for (const char of searchTerm) {
                input.value += char;
                await new Promise(r => setTimeout(r, Math.random() * 50 + 50));
            }
            mgr.increment(isMobile);
            setTimeout(() => btn.click(), 800);
        }
    }

    // --- 5. 主控制器 (Main Controller) ---
    async function main() {
        // 关键：重新实例化一次 RewardManager 以获取最新的本地存储数据
        // 或者手动调用一次数据同步逻辑
        const stored = JSON.parse(GM_getValue("bing_progress", "{}"));
        if (stored.date === mgr.progress.date) {
            mgr.progress = stored;
        }
        if (mgr.isAllDone()) {
            ui.updateStatus("ALL COMPLETED!");
            return;
        }

        if (isRunning) return;
        isRunning = true;

        let delay = Math.floor(Math.random() * (80 - 60 + 1)) + 60;
        if (rewardInterval) clearInterval(rewardInterval);

        rewardInterval = setInterval(async () => {
            if (isPaused) return;

            ui.updateStatus(`${delay}s`);
            if (delay <= 0) {
                clearInterval(rewardInterval);
                ui.updateStatus("Searching...");
                isRunning = false; // 释放锁
                await performSearch();
            }
            delay--;
        }, 1000);
    }

    const ui = new RewardUI();
    main();

    interceptNavigation(() => {
        console.info("[BingRewards] SPA Navigation. Restarting...");
        isRunning = false;
        setTimeout(main, 1500);
    });
})();