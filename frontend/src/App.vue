<template>
  <div class="layout">
    <header class="header">
      <h1>BetterStock 智能投研平台</h1>
      <p>新闻聚合 · 行情监控 · 智能选股 · 回测分析</p>
    </header>
    <main class="content">
      <section class="panel">
        <h2>实时行情</h2>
        <button @click="loadQuotes" :disabled="loading.quotes">
          {{ loading.quotes ? '加载中...' : '刷新行情' }}
        </button>
        <table>
          <thead>
            <tr>
              <th>代码</th>
              <th>名称</th>
              <th>最新价</th>
              <th>涨跌幅</th>
              <th>换手率</th>
              <th>行业</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="quote in quotes" :key="quote.ticker">
              <td>{{ quote.ticker }}</td>
              <td>{{ quote.name }}</td>
              <td>{{ quote.price.toFixed(2) }}</td>
              <td :class="{ up: quote.percent_change > 0, down: quote.percent_change < 0 }">
                {{ quote.percent_change.toFixed(2) }}%
              </td>
              <td>{{ quote.turnover_rate.toFixed(2) }}%</td>
              <td>{{ quote.industry }}</td>
            </tr>
          </tbody>
        </table>
      </section>
      <section class="panel">
        <h2>新闻与情感</h2>
        <button @click="refreshNews" :disabled="loading.news">
          {{ loading.news ? '刷新中...' : '抓取最新新闻' }}
        </button>
        <ul class="news-list">
          <li v-for="article in news" :key="article.id">
            <h3>{{ article.title }}</h3>
            <p class="meta">{{ formatDate(article.published_at) }} · {{ article.source }}</p>
            <p>{{ article.summary }}</p>
            <div class="sentiment" v-if="article.sentiments?.length">
              情感得分:
              <span :class="{ up: article.sentiments[0].sentiment > 0, down: article.sentiments[0].sentiment < 0 }">
                {{ article.sentiments[0].sentiment.toFixed(2) }}
              </span>
              (置信度 {{ (article.sentiments[0].confidence * 100).toFixed(0) }}%)
            </div>
          </li>
        </ul>
      </section>
      <section class="panel">
        <h2>智能选股评分</h2>
        <button @click="loadScores" :disabled="loading.scores">
          {{ loading.scores ? '计算中...' : '获取评分' }}
        </button>
        <table>
          <thead>
            <tr>
              <th>代码</th>
              <th>名称</th>
              <th>综合评分</th>
              <th>情绪</th>
              <th>行业</th>
              <th>技术</th>
              <th>基本面</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="score in scores" :key="score.ticker">
              <td>{{ score.ticker }}</td>
              <td>{{ score.name }}</td>
              <td>{{ score.score.toFixed(3) }}</td>
              <td>{{ (score.components.sentiment ?? 0).toFixed(3) }}</td>
              <td>{{ (score.components.industry ?? 0).toFixed(3) }}</td>
              <td>{{ (score.components.technical ?? 0).toFixed(3) }}</td>
              <td>{{ (score.components.fundamental ?? 0).toFixed(3) }}</td>
            </tr>
          </tbody>
        </table>
      </section>
      <section class="panel">
        <h2>回测报告</h2>
        <button @click="runBacktest" :disabled="loading.backtest">
          {{ loading.backtest ? '执行中...' : '运行回测' }}
        </button>
        <div v-if="backtest">
          <p>区间: {{ formatDate(backtest.started_at) }} - {{ formatDate(backtest.ended_at) }}</p>
          <p>总收益: {{ (backtest.total_return * 100).toFixed(2) }}%</p>
          <p>年化: {{ (backtest.annualized_return * 100).toFixed(2) }}%</p>
          <p>最大回撤: {{ (backtest.max_drawdown * 100).toFixed(2) }}%</p>
          <p>夏普比率: {{ backtest.sharpe_ratio.toFixed(2) }}</p>
          <h3>最新持仓</h3>
          <ul>
            <li v-for="trade in backtest.trades" :key="trade.ticker">
              {{ trade.ticker }} - {{ trade.action }} - 权重 {{ (trade.weight * 100).toFixed(1) }}%
            </li>
          </ul>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import axios from 'axios';

const quotes = ref([]);
const news = ref([]);
const scores = ref([]);
const backtest = ref(null);

const loading = reactive({
  quotes: false,
  news: false,
  scores: false,
  backtest: false,
});

const formatDate = (value) => new Date(value).toLocaleString();

const loadQuotes = async () => {
  loading.quotes = true;
  try {
    const { data } = await axios.get('/api/market/quotes');
    quotes.value = data.map((item) => ({
      ...item,
      percent_change: item.percent_change,
    }));
  } finally {
    loading.quotes = false;
  }
};

const refreshNews = async () => {
  loading.news = true;
  try {
    await axios.post('/api/news/refresh');
    const { data } = await axios.get('/api/news/latest');
    news.value = data;
  } finally {
    loading.news = false;
  }
};

const loadScores = async () => {
  loading.scores = true;
  try {
    const { data } = await axios.get('/api/analytics/scores');
    scores.value = data;
  } finally {
    loading.scores = false;
  }
};

const runBacktest = async () => {
  loading.backtest = true;
  try {
    const { data } = await axios.post('/api/backtest/run');
    backtest.value = data;
  } finally {
    loading.backtest = false;
  }
};

onMounted(async () => {
  await Promise.all([loadQuotes(), refreshNews(), loadScores()]);
});
</script>

<style scoped>
.layout {
  font-family: 'Helvetica Neue', Arial, sans-serif;
  margin: 0 auto;
  max-width: 1200px;
  padding: 24px;
  color: #1f2933;
  background: #f7fafc;
}

.header {
  text-align: center;
  margin-bottom: 24px;
}

.content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.panel {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.08);
}

.panel h2 {
  margin-top: 0;
}

button {
  padding: 6px 12px;
  margin-bottom: 12px;
  border: none;
  border-radius: 6px;
  background-color: #2563eb;
  color: #fff;
  cursor: pointer;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 6px 8px;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

.news-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.news-list li {
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.meta {
  color: #64748b;
  font-size: 14px;
}

.sentiment {
  margin-top: 8px;
  font-weight: 600;
}

.up {
  color: #16a34a;
}

.down {
  color: #dc2626;
}
</style>
