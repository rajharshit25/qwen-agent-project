const $=id=>document.getElementById(id);
const API="http://127.0.0.1:8000/api";
async function currentPage(){
 const [tab]=await chrome.tabs.query({active:true,currentWindow:true});
 if(!tab?.id||!/^https?:/.test(tab.url||"")) throw new Error("Chrome internal/restricted pages cannot be read.");
 try {
  const r=await chrome.tabs.sendMessage(tab.id,{type:"QWEN_EXTRACT_PAGE"});
  if(!r?.ok) throw new Error(r?.error||"Extraction failed");
  return r.page;
 } catch(e){throw new Error("Could not extract page. Reload the tab and retry. "+e.message);}
}
async function post(path,body){
 const res=await fetch(API+path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
 const data=await res.json().catch(()=>({detail:"Invalid backend response"}));
 if(!res.ok) throw new Error(data.detail||`Backend returned ${res.status}`);
 return data;
}
async function run(kind){
 $("answer").textContent="Working…";$("trace").textContent="";$("status").textContent="Connecting to local backend…";
 $("summarize").disabled=$("ask").disabled=true;
 try {
  let data;
  if(kind==="summarize"){
   const p=await currentPage();
   data=await post("/summarize",{text:`Title: ${p.title}\nURL: ${p.url}\nHeadings: ${p.headings.join(" | ")}\n\n${p.text}`});
   $("answer").textContent=data.summary;
  } else {
   const q=$("question").value.trim();if(!q) throw new Error("Enter a question first.");
   let page_text="";
   if(/\b(page|article|website|this)\b/i.test(q)){const p=await currentPage();page_text=`Title: ${p.title}\nURL: ${p.url}\n${p.text}`;}
   data=await post("/agent",{goal:q,page_text});
   $("answer").textContent=data.answer;$("trace").textContent=JSON.stringify(data.trace,null,2);
  }
  $("status").textContent="Completed.";
 } catch(e){$("answer").textContent="Error: "+e.message;$("status").textContent="Request failed.";}
 finally{$("summarize").disabled=$("ask").disabled=false;}
}
$("summarize").addEventListener("click",()=>run("summarize"));
$("ask").addEventListener("click",()=>run("ask"));
