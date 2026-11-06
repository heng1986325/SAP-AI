#!/usr/bin/env node
/**
 * build-skill.mjs
 *
 * 构建 abap-cdc-gen skill 的 bundle.json
 *
 * 读取 references/*.md → 解析为结构化 JSON → 输出 minified build/bundle.json
 *
 * 用法: node build-skill.mjs
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = __dirname;
const REF_DIR = path.join(SKILL_DIR, 'references');
const OUT_DIR = path.join(SKILL_DIR, 'build');
const OUT_FILE = path.join(OUT_DIR, 'bundle.json');

// ── 文件映射 ──
const FILE_MAP = [
  { file: 'abap-workflow.md',     key: 'workflow' },
  { file: 'safety.md',            key: 'safety' },
  { file: 'abap-coding.md',       key: 'standards.coding' },
  { file: 'abap-class.md',        key: 'standards.class' },
  { file: 'abap-interface.md',    key: 'standards.interface' },
  { file: 'abap-batchinput.md',   key: 'standards.batchinput' },
  { file: 'feishu-bitable.md',    key: 'feishu' },
  { file: 'rest-api.md',          key: 'rest_api' },
];

// ── 解析器 ──

/**
 * 去除 frontmatter (--- 之间的 YAML 头)
 */
function stripFrontmatter(text) {
  return text.replace(/^---[\s\S]*?---\n*/, '').trim();
}

/**
 * 把 Markdown 解析为结构化段落数组
 * 每段: { heading, level, content, subitems? }
 */
function parseMarkdown(text) {
  const body = stripFrontmatter(text);
  const lines = body.split('\n');
  const sections = [];
  let current = null;
  let inCodeBlock = false;
  let codeBlockLang = '';
  let codeLines = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // 代码块开关
    if (/^```/.test(line)) {
      if (!inCodeBlock) {
        inCodeBlock = true;
        codeBlockLang = line.slice(3).trim();
        codeLines = [];
      } else {
        inCodeBlock = false;
        // 把代码块追加到当前段
        if (current) {
          if (!current.codeBlocks) current.codeBlocks = [];
          current.codeBlocks.push({
            lang: codeBlockLang,
            code: codeLines.join('\n'),
          });
        }
        codeBlockLang = '';
        codeLines = [];
      }
      continue;
    }
    if (inCodeBlock) {
      codeLines.push(line);
      continue;
    }

    // 标题
    const headingMatch = line.match(/^(#{1,6})\s+(.+)/);
    if (headingMatch) {
      current = {
        heading: headingMatch[2].trim(),
        level: headingMatch[1].length,
        content: '',
        codeBlocks: [],
        table: null,
        list: [],
      };
      sections.push(current);
      continue;
    }

    if (!current) {
      // 正文开头（标题前的内容）
      current = {
        heading: '',
        level: 0,
        content: '',
        codeBlocks: [],
        table: null,
        list: [],
      };
      sections.push(current);
    }

    // 表格
    const tableMatch = line.match(/^\|.+\|$/);
    if (tableMatch) {
      if (!current.table) current.table = [];
      // 跳过分隔行 (|---|)
      if (/^\|[\s\-:]+\|$/.test(line)) continue;
      const cells = line.split('|').slice(1, -1).map(c => c.trim());
      current.table.push(cells);
      continue;
    }

    // 列表项
    const listMatch = line.match(/^\s*[-*+]\s+(.+)/);
    if (listMatch) {
      current.list.push(listMatch[1].trim());
      continue;
    }

    // 普通文本
    if (current.content) current.content += '\n';
    current.content += line;
  }

  // 清理空段
  return sections.filter(s => s.heading || s.content.trim() || s.codeBlocks.length || s.table || s.list.length);
}

/**
 * 按点号分隔的 key 写入嵌套对象
 */
function setNested(obj, key, value) {
  const keys = key.split('.');
  let cur = obj;
  for (let i = 0; i < keys.length - 1; i++) {
    if (!cur[keys[i]]) cur[keys[i]] = {};
    cur = cur[keys[i]];
  }
  cur[keys[keys.length - 1]] = value;
}

// ── 主流程 ──

function build() {
  const bundle = {};

  for (const { file, key } of FILE_MAP) {
    const filePath = path.join(REF_DIR, file);
    if (!fs.existsSync(filePath)) {
      console.warn(`⚠ 文件不存在，跳过: ${file}`);
      continue;
    }
    const content = fs.readFileSync(filePath, 'utf-8');
    const sections = parseMarkdown(content);
    setNested(bundle, key, sections);
    console.log(`  ✓ ${file} → ${key} (${sections.length} sections)`);
  }

  // 写入
  if (!fs.existsSync(OUT_DIR)) {
    fs.mkdirSync(OUT_DIR, { recursive: true });
  }

  // minified JSON（无空格，单行）
  const json = JSON.stringify(bundle);
  fs.writeFileSync(OUT_FILE, json, 'utf-8');

  const kb = (json.length / 1024).toFixed(1);
  console.log(`\n  ✓ 写入 ${OUT_FILE} (${kb} KB)`);
}

build();