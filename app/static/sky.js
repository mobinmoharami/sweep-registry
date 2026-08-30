
(function(){
  var c=document.getElementById('sky');
  if(!c||window.matchMedia('(prefers-reduced-motion:reduce)').matches)return;
  var x=c.getContext('2d'),s=[],w,h;
  function size(){w=c.width=innerWidth;h=c.height=innerHeight;s=[];
    var n=Math.min(180,Math.round(w*h/12000));
    for(var i=0;i<n;i++)s.push({x:Math.random()*w,y:Math.random()*h,
      r:Math.random()*1.1+.2,a:Math.random()*.5+.15,v:Math.random()*.02+.004});}
  function draw(t){x.clearRect(0,0,w,h);
    for(var i=0;i<s.length;i++){var p=s[i];var f=p.a+Math.sin(t*p.v+i)*.18;
      x.beginPath();x.arc(p.x,p.y,p.r,0,6.283);
      x.fillStyle='rgba(180,205,240,'+Math.max(0,f)+')';x.fill();}
    requestAnimationFrame(draw);}
  size();requestAnimationFrame(draw);addEventListener('resize',size);
})();
