export default class WS{
constructor(url){
this.url = url
this.ws = new WebSocket(url)
this.onmessage = ()=>{}
this.ws.onopen = ()=> console.log('ws open')
this.ws.onmessage = (ev)=>{
if(this.onmessage) this.onmessage(ev.data)
}
this.ws.onclose = ()=> console.log('ws closed')
}
close(){ this.ws.close() }
}