const assert = require("node:assert/strict");
const { calculateQuote } = require("../assets/quote-comparison-v1.js");
const fixed = {mode:"fixed",base:"500",rate:"10",minimum:"0",setup:"0"};
const percent = {mode:"percentage",base:"0",rate:"10",minimum:"400",setup:"300"};
assert.deepEqual(calculateQuote("3000",3,fixed), {monthlyFeeCents:50000,firstMonthCents:350000,serviceTotalCents:150000,termTotalCents:1050000});
assert.deepEqual(calculateQuote("3000",3,percent), {monthlyFeeCents:40000,firstMonthCents:370000,serviceTotalCents:150000,termTotalCents:1050000});
assert.deepEqual(calculateQuote("3000",3,{...percent,mode:"hybrid",base:"200",rate:"5",setup:"100"}), {monthlyFeeCents:40000,firstMonthCents:350000,serviceTotalCents:130000,termTotalCents:1030000});
assert.equal(calculateQuote("10000",1,percent).monthlyFeeCents,100000);
assert.equal(calculateQuote("0.05",3,{...percent,minimum:"0",setup:"0"}).serviceTotalCents,3);
assert.equal(calculateQuote("0.05",3,{...percent,minimum:"0",setup:"0"}).termTotalCents,18);
assert.equal(calculateQuote("0","3.0",{...fixed,base:"0"}).termTotalCents,0);
assert.equal(calculateQuote("3000",3,{...fixed,rate:"invalid",minimum:"invalid"}).termTotalCents,1050000);
assert.equal(calculateQuote("3000",3,{...percent,base:"invalid"}).termTotalCents,1050000);
assert.equal(calculateQuote("1000000",120,{mode:"hybrid",base:"1000000",rate:"100",minimum:"1000000",setup:"1000000"}).termTotalCents,36100000000);
for (const amount of ["", "-1", "1.005", "NaN", "Infinity", "1000000.01", "999999999999999999999999999"]) {
  assert.throws(()=>calculateQuote(amount,3,fixed),RangeError);
}
for (const month of ["",0,-1,1.5,121,"Infinity"]) assert.throws(()=>calculateQuote("3000",month,fixed),RangeError);
for (const quote of [{...fixed,mode:"other"},{...percent,rate:"100.01"},{...percent,minimum:""},{...fixed,setup:"-0.01"}]) {
  assert.throws(()=>calculateQuote("3000",3,quote),RangeError);
}
console.log("Quote arithmetic, half-cent rounding, minimums, setup-once, inactive fields and invalid boundaries passed");
