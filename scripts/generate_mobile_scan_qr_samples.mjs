#!/usr/bin/env node
import { createRequire } from 'node:module'
import { mkdir, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

class SvgElementShim {
  constructor(tagName) {
    this.tagName = tagName
    this.attributes = new Map()
    this.children = []
    this.textContent = ''
  }

  setAttribute(name, value) {
    this.attributes.set(name, String(value))
  }

  setAttributeNS(_namespace, name, value) {
    this.setAttribute(name, value)
  }

  appendChild(child) {
    this.children.push(child)
    return child
  }

  get outerHTML() {
    const attrs = [...this.attributes.entries()]
      .map(([key, value]) => ` ${key}="${escapeXml(value)}"`)
      .join('')
    const children = this.children.map(child => child.outerHTML ?? escapeXml(String(child))).join('')
    const text = this.textContent ? escapeXml(this.textContent) : ''
    return `<${this.tagName}${attrs}>${text}${children}</${this.tagName}>`
  }
}

function escapeXml(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('"', '&quot;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
}

if (typeof globalThis.document === 'undefined') {
  globalThis.document = {
    createElementNS: (_namespace, tagName) => new SvgElementShim(tagName)
  }
}

const require = createRequire(import.meta.url)
const { BrowserQRCodeSvgWriter } = require('../frontend/node_modules/@zxing/library')

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = resolve(__dirname, '..')
const outputDir = resolve(root, 'docs/acceptance/mobile-scan-samples')

const samples = [
  {
    name: 'record_DEMO_PENDING_R1',
    value: 'record_DEMO_PENDING_R1',
    purpose: '待接收记录：用于真机扫码验收接收提交路径'
  },
  {
    name: 'record_DEMO_RECEIVED_R1',
    value: 'record_DEMO_RECEIVED_R1',
    purpose: '已接收记录：用于真机扫码验收发出提交路径'
  },
  {
    name: 'bad_code_for_field_test',
    value: 'bad_code_for_field_test',
    purpose: '无效码：用于现场异常提示与不可提交路径验证'
  }
]

const writer = new BrowserQRCodeSvgWriter()
await mkdir(outputDir, { recursive: true })

const indexRows = []
for (const sample of samples) {
  const svg = writer.write(sample.value, 320, 320)
  const svgText = `${svg.outerHTML}\n`
  const filename = `${sample.name}.svg`
  await writeFile(resolve(outputDir, filename), svgText, 'utf8')
  indexRows.push(`| ${sample.name} | \`${sample.value}\` | [${filename}](./${filename}) | ${sample.purpose} |`)
}

const indexMarkdown = `# 手机摄像头扫码现场验收样张\n\n这些二维码样张由 \`scripts/generate_mobile_scan_qr_samples.mjs\` 使用 \`@zxing/library\` 的 \`BrowserQRCodeSvgWriter\` 生成，用于 P0 真机扫码验收支撑。\n\n> 注意：样张生成完成未等于真机已通过，仍需按现场清单使用手机访问 HTTPS 地址进行扫码、提交、API/DB 回查。\n\n| 样张 | 码值 | SVG | 用途 |\n| --- | --- | --- | --- |\n${indexRows.join('\n')}\n\n## 重新生成\n\n\`\`\`bash\nnode scripts/generate_mobile_scan_qr_samples.mjs\n\`\`\`\n`

await writeFile(resolve(outputDir, 'index.md'), indexMarkdown, 'utf8')
console.log(`Generated ${samples.length} mobile scan QR samples in docs/acceptance/mobile-scan-samples`)
