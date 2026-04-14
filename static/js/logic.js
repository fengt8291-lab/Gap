var MC=[-1,0,0,1,2];
var dimMap={1:"criticism",2:"defensive",3:"indifference",4:"taking",5:"criticism",6:"defensive",7:"indifference",8:"taking",9:"criticism",10:"indifference",11:"indifference",12:"defensive",13:"criticism",14:"narcissism",15:"narcissism",16:"forgetful",17:"forgetful",18:"taking",19:"narcissism",20:"criticism",21:"indifference",22:"narcissism",23:"forgetful",24:"defensive",25:"taking"};
var dimMax={criticism:14,indifference:14,defensive:12,taking:12,narcissism:12,forgetful:10};
var TOTAL_MAX=70;
var DIM_ORDER=['criticism','indifference','narcissism','forgetful','defensive','taking'];
var DIM_LABELS={criticism:'谦逊度',indifference:'关怀度',narcissism:'自信度',forgetful:'细心度',defensive:'开放度',taking:'慷慨度'};
var DIM_COLORS={criticism:'#e74c3c',indifference:'#95a5a6',narcissism:'#f39c12',forgetful:'#9b59b6',defensive:'#e67e22',taking:'#1abc9c'};

function getScores(){var p=new URLSearchParams(window.location.search);var r={};for(var i=1;i<=25;i++){var v=p.get('q'+i);r[i]=v!==null?parseInt(v):0;}return r;}
function calcDims(scores){var d={criticism:0,indifference:0,narcissism:0,forgetful:0,defensive:0,taking:0};for(var q=1;q<=25;q++){var dm=dimMap[q];if(!dm)continue;d[dm]+=(q>=20)?scores[q]:Math.max(0,MC[scores[q]]);}return d;}
function healthOf(dims){var h={};for(var k in dims)h[k]=Math.max(0,Math.round(100-dims[k]/dimMax[k]*100));return h;}
function fc(p){return p>=70?'#2ecc71':p>=50?'#f39c12':'#e74c3c';}

function drawRadar(h,dims){
    var svg=document.getElementById('radar-svg');
    var cx=150,cy=150,r=95,html='';
    for(var ring=1;ring<=4;ring++)html+='<circle cx="'+cx+'" cy="'+cy+'" r="'+(r*ring/4)+'" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>';
    for(var i=0;i<6;i++){
        var a=(i*60-90)*Math.PI/180;
        var x2=cx+r*Math.cos(a),y2=cy+r*Math.sin(a);
        html+='<line x1="'+cx+'" y1="'+cy+'" x2="'+x2+'" y2="'+y2+'" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>';
        var lx=cx+(r+18)*Math.cos(a),ly=cy+(r+18)*Math.sin(a);
        html+='<text x="'+lx+'" y="'+ly+'" text-anchor="middle" dominant-baseline="middle" fill="'+DIM_COLORS[DIM_ORDER[i]]+'" font-size="10" font-weight="500">'+DIM_LABELS[DIM_ORDER[i]]+'</text>';
    }
    var pts=DIM_ORDER.map(function(d,i){var a=(i*60-90)*Math.PI/180;var pr=h[d]/100*r;return(cx+pr*Math.cos(a))+','+(cy+pr*Math.sin(a));});
    html+='<polygon points="'+pts.join(' ')+'" fill="rgba(46,204,113,0.18)" stroke="#2ecc71" stroke-width="2"/>';
    DIM_ORDER.forEach(function(d,i){var a=(i*60-90)*Math.PI/180;var pr=h[d]/100*r;html+='<circle cx="'+(cx+pr*Math.cos(a))+'" cy="'+(cy+pr*Math.sin(a))+'" r="5" fill="'+DIM_COLORS[d]+'" stroke="#fff" stroke-width="2"/>';});
    svg.innerHTML=html;
    var leg='';
    DIM_ORDER.forEach(function(d){var c=fc(h[d]);leg+='<div class="legend-item"><span class="legend-dot" style="background:'+c+'"></span>'+DIM_LABELS[d]+' '+h[d]+'%</div>';});
    document.getElementById('radar-legend').innerHTML=leg;
}

function toggleDim(idx){var b=document.getElementById('dim-body-'+idx);var t=document.getElementById('dim-toggle-'+idx);if(b.classList.contains('open')){b.classList.remove('open');t.classList.remove('open');}else{b.classList.add('open');t.classList.add('open');}}

function shuffle(arr){var a=arr.slice();for(var i=a.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=a[i];a[i]=a[j];a[j]=t;}return a;}

function renderBooks(){
    var cards=document.querySelectorAll('.book-card');
    var picks=shuffle(ALL_BOOKS).slice(0,3);
    cards.forEach(function(card,idx){
        if(idx<picks.length){
            var b=picks[idx];
            card.querySelector('.book-title').textContent=b.Title;
            card.querySelector('.book-author').textContent=b.Author;
            card.querySelector('.book-desc').textContent=b.Desc;
            card.style.display='flex';
        } else {
            card.style.display='none';
        }
    });
}

function renderReport(){
    var scores=getScores();
    var dims=calcDims(scores);
    var h=healthOf(dims);
    var sorted=Object.entries(dims).sort(function(a,b){return b[1]-a[1];});
    var main=sorted[0];
    var safeDims=Object.entries(dims).filter(function(kv){return h[kv[0]]>=70;});
    var total=Object.values(dims).reduce(function(a,b){return a+b;},0);
    var overall=Math.max(0,Math.round(100-total/TOTAL_MAX*100));
    var hc=document.getElementById('health-card');
    var hs=document.getElementById('health-score');
    var hd=document.getElementById('health-desc');
    var hl=document.getElementById('health-label');
    hs.textContent=overall;
    if(overall<50){hc.style.borderColor='rgba(231,76,60,0.3)';hc.style.background='rgba(231,76,60,0.08)';hs.style.color='#e74c3c';hd.style.color='#e74c3c';hl.style.color='#e74c3c';hd.textContent='核心弱点明显，建议重点关注并改进';}
    else if(overall<70){hc.style.borderColor='rgba(243,156,18,0.3)';hc.style.background='rgba(243,156,18,0.08)';hs.style.color='#f39c12';hd.style.color='#f39c12';hl.style.color='#f39c12';hd.textContent='多个维度有信号，需要有意识地调整';}
    else if(overall<85){hc.style.borderColor='rgba(46,204,113,0.25)';hc.style.background='rgba(46,204,113,0.08)';hs.style.color='#2ecc71';hd.style.color='#8892b0';hl.style.color='#2ecc71';hd.textContent='整体良好，有1-2个维度需要注意';}
    else{hc.style.borderColor='rgba(46,204,113,0.25)';hc.style.background='rgba(46,204,113,0.08)';hs.style.color='#2ecc71';hd.style.color='#8892b0';hl.style.color='#2ecc71';hd.textContent='恭喜！各指标健康，你的人际模式非常健康';}
    drawRadar(h,dims);
    var mainD=dimData[main[0]];
    document.getElementById('main-icon').textContent=mainD.icon;
    document.getElementById('main-name').textContent=mainD.name;
    document.getElementById('main-desc').textContent=mainD.desc;
    document.getElementById('main-score').textContent=h[main[0]]+'%';
    document.getElementById('carnegie-quote').textContent=mainD.quote;
    document.getElementById('why-section').textContent=mainD.why;
    document.getElementById('carnegie-why-block').textContent=mainD.carnegieWhy;
    document.getElementById('impact-section').textContent=mainD.impact;
    document.getElementById('carnegie-impact-block').textContent=mainD.carnegieImpact;
    var actHtml='';
    mainD.actions.forEach(function(a,i){actHtml+='<div class="action-card"><span class="action-num">'+(i+1)+'</span><span class="action-text">'+a+'</span></div>';});
    document.getElementById('action-tips').innerHTML=actHtml;
    var dimCardsHtml='';
    DIM_ORDER.forEach(function(d,i){var dd=dimData[d];var pct=h[d];var c=fc(pct);dimCardsHtml+='<div class="dim-card"><div class="dim-card-header" onclick="toggleDim('+i+')"><div class="dim-header-left"><span class="dim-icon">'+dd.icon+'</span><span class="dim-name">'+dd.name+'</span></div><div class="dim-health-bar-wrap"><div class="dim-health-bar"><div class="dim-health-fill" style="width:'+pct+'%;background:'+c+'"></div></div></div><span class="dim-health-pct" style="color:'+c+'">'+pct+'%</span><span class="dim-toggle" id="dim-toggle-'+i+'">&#9660;</span></div><div class="dim-card-body" id="dim-body-'+i+'"><p class="dim-intro">'+dd.intro+'</p><p class="dim-quote">'+dd.carnegieWhy+'</p></div></div>';});
    document.getElementById('dim-cards').innerHTML=dimCardsHtml;
    if(safeDims.length>0){var sh='';safeDims.forEach(function(kv){var sd=dimData[kv[0]];sh+='<div class="safe-card"><span class="safe-icon">'+sd.icon+'</span><span class="safe-name">'+sd.name+'</span>（'+h[kv[0]]+'%）— 这方面你表现健康！</div>';});document.getElementById('safe-weakness').innerHTML=sh;}
    else{document.getElementById('safe-section').style.display='none';}
    renderBooks();
    var shareBtn=document.getElementById('share-btn');
    shareBtn.onclick=function(){
        var mn=document.getElementById('main-name').textContent;
        var mp=document.getElementById('main-score').textContent;
        var qt=mainD.quote.substring(0,45);
        var LS='\u2028';
        var txt='我在【测测你的人性弱点】中发现了自己的短板：'+LS+LS+mainD.icon+' '+mn+'（'+mp+'）'+LS+LS+qt+'...'+LS+LS+'卡耐基说这是人际关系的杀手'+LS+'快来测测你的 ↓';
        if(navigator.clipboard)navigator.clipboard.writeText(txt).then(function(){alert('已复制！去小红书/朋友圈分享吧~');});
    };
}
renderReport();
