import { useEffect, useRef } from 'react';
import * as echarts from 'echarts/core';
import { LineChart, ScatterChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, MarkAreaComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { EChartsOption } from 'echarts';
import type { Reading } from './api';

echarts.use([LineChart, ScatterChart, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, MarkAreaComponent, CanvasRenderer]);

export function RiskChart({ readings, compareReadings = [], dark, compact = false }: {
  readings: Reading[];
  compareReadings?: Reading[];
  dark: boolean;
  compact?: boolean;
}) {
  const element = useRef<HTMLDivElement>(null);
  const chart = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!element.current) return;
    chart.current = echarts.init(element.current);
    const observer = new ResizeObserver(() => chart.current?.resize());
    observer.observe(element.current);
    return () => { observer.disconnect(); chart.current?.dispose(); chart.current = null; };
  }, []);

  useEffect(() => {
    const text = dark ? '#a6aaa9' : '#837c70';
    const border = dark ? 'rgba(255,255,255,.07)' : '#e9e3d9';
    const valid = readings.filter((reading) => reading.event_type === 'cut');
    const compare = compareReadings.filter((reading) => reading.event_type === 'cut');
    const option: EChartsOption = {
      animationDuration: 250,
      grid: { left: 40, right: 16, top: compact ? 12 : 22, bottom: 32 },
      textStyle: { fontFamily: 'Inter, sans-serif' },
      tooltip: {
        trigger: 'axis',
        backgroundColor: dark ? '#24272b' : '#faf9f6',
        borderColor: border,
        textStyle: { color: dark ? '#f5f5f4' : '#292823', fontSize: 12 },
        valueFormatter: (value) => typeof value === 'number' ? (value * 100).toFixed(1) + '%' : 'Unavailable',
      },
      xAxis: {
        type: 'value', minInterval: 1,
        axisLabel: { color: text, fontSize: 10 },
        axisLine: { lineStyle: { color: border } }, axisTick: { show: false },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value', min: 0, max: 1,
        axisLabel: { color: text, fontSize: 10, formatter: (value: number) => Math.round(value * 100) + '%' },
        splitLine: { lineStyle: { color: border, type: 'dashed' } },
      },
      series: [
        {
          name: 'Damage within 5 cuts', type: 'line', smooth: false, showSymbol: false,
          data: valid.map((reading) => [reading.cycle, reading.decision?.risk ?? null]),
          connectNulls: false, lineStyle: { color: '#ef7847', width: 2.5 },
          areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(240,90,40,.19)' }, { offset: 1, color: 'rgba(240,90,40,0)' }]) },
        },
        {
          name: 'Actionable risk', type: 'line', smooth: false, showSymbol: false,
          data: valid.map((reading) => [reading.cycle, reading.decision?.actionable_risk ?? null]),
          connectNulls: false, lineStyle: { color: dark ? '#8dcbb5' : '#5d8979', width: 1.5, type: 'dashed' },
        },
        {
          name: 'Periodic policy', type: 'line', smooth: false, showSymbol: false,
          data: compare.map((reading) => [reading.cycle, reading.decision?.risk ?? null]),
          lineStyle: { color: '#8a98ba', width: 2 },
        },
        {
          name: 'Vibration released', type: 'scatter', symbol: 'diamond', symbolSize: 7,
          data: valid.filter((reading) => reading.vibration_released).map((reading) => [reading.cycle, reading.decision?.risk ?? 0]),
          itemStyle: { color: '#d8a33c', borderColor: dark ? '#15181e' : '#faf9f6', borderWidth: 1 },
        },
      ],
    };
    chart.current?.setOption(option, { notMerge: true });
  }, [readings, compareReadings, dark, compact]);

  return <div className={'risk-chart' + (compact ? ' compact' : '')} ref={element} role="img" aria-label="Predicted benchmark damage risk over completed cuts. Values available in the evidence table." />;
}
