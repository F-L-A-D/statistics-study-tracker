/* Run: node scripts/test_lecture_view.js */
const fs=require("node:fs");
const vm=require("node:vm");
const assert=require("node:assert/strict");
const L=JSON.parse(fs.readFileSync("data/lectures.json","utf8")).lectures;
const pages=["practice.html","lectures.html"].map(p=>fs.readFileSync(p,"utf8"));
const context={window:{},console};
vm.runInNewContext(fs.readFileSync("lecture-view.js","utf8"),context);
const view=context.window.LectureView;
assert.ok(view && view.markup && view.textBlocks);
const ids=["T003","T023","T042","T054","T077","T001","T025","T043","T057","T094","T007","T030","T051","T062","T104"];
for(const id of ids){
 const lecture=L[id];assert.ok(lecture,id);
 const html=view.markup(lecture);
 assert.match(html,/class="lecture-equation"/);
 assert.match(html,/class="lecture-section"/);
 assert.ok(!html.includes('class="math-prose"'));
 const count=(html.match(/data-lecture-tex=/g)||[]).length;
 assert.ok(count>=2,id+" needs block maths; got "+count);
}
const example=view.textBlocks('前置き \\(x^2+1\\) 後置き \\[\\frac{1}{2}\\]');
assert.equal((example.match(/class="lecture-equation"/g)||[]).length,2);
assert.ok(!example.includes('\\(') && !example.includes('\\['));
// Standalone TeX blocks should never inherit Japanese punctuation on either side.
const punct=view.textBlocks('ベイズの定理は、 \(P(A\mid B)=0.25\)。分母は全確率、 \[P(B)=0.5\]。次の説明は続く。');
assert.ok(punct.includes('<p class="lecture-prose">ベイズの定理は</p>'),punct);
assert.ok(punct.includes('<p class="lecture-prose">分母は全確率</p>'),punct);
assert.ok(punct.includes('<p class="lecture-prose">次の説明は続く。</p>'),punct);
assert.equal((punct.match(/class="lecture-equation"/g)||[]).length,2);
assert.ok(!punct.includes('>。</p>') && !punct.includes('>、</p>'),punct);
assert.ok(!punct.includes('>。分母') && !punct.includes('>、分母'),punct);
assert.ok(punct.includes('0.25') && punct.includes('0.5'),"Decimals inside TeX must be preserved");
const plain=view.textBlocks('通常の説明文。句読点、は維持する。');
assert.ok(plain.includes('通常の説明文。句読点、は維持する。'),plain);
for(const page of pages){
 assert.ok(page.includes('src="./lecture-view.js"'),"Missing common renderer import");
 assert.ok(page.includes('href="./lecture-view.css"'),"Missing shared CSS");
 assert.ok(page.includes('LectureView.markup('),"Missing common lecture renderer");
 assert.ok(page.includes('LectureView.renderMath('),"Missing block math rendering");
}
assert.ok(pages[0].includes('LectureView.textBlocks(q.question)'));
assert.ok(pages[0].includes('function copySet()'));
console.log('PASS: shared block math, punctuation boundaries, source prose, answer copy, and 15 topic lectures');
