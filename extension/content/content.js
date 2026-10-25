function extractPage() {
  return {
    title: document.title || "",
    url: location.href,
    headings: Array.from(document.querySelectorAll("h1,h2,h3")).slice(0,40).map(x=>x.innerText.trim()).filter(Boolean),
    links: Array.from(document.querySelectorAll("a[href]")).slice(0,30).map(a=>({text:(a.innerText||"").trim().slice(0,120),url:a.href})),
    text: document.body ? (document.body.innerText||"").slice(0,12000) : ""
  };
}
chrome.runtime.onMessage.addListener((msg,sender,sendResponse)=>{
  if(msg?.type==="QWEN_EXTRACT_PAGE") {
    try { sendResponse({ok:true,page:extractPage()}); }
    catch(e) { sendResponse({ok:false,error:String(e)}); }
  }
  return true;
});
