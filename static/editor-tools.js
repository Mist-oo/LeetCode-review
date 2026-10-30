'use strict';

function setupEditorPairing(cm) {
  // The upstream addon supplies pairing/surround/delete. Python quote input
  // needs literal escaped quotes and one-character closing-triple traversal.
  function quoteKey(quote) {
    return editor => {
      if(editor.getOption('readOnly')||editor.getOption('disableInput'))return CodeMirror.Pass;
      const actions=editor.listSelections().map(range=>{
        if(!range.empty())return null;
        const pos=range.head,line=editor.getLine(pos.line),before=line.slice(0,pos.ch);
        if((before.match(/\\+$/)?.[0].length||0)%2)return 'insert';
        const token=editor.getTokenAt(pos,true),type=token.type||'';
        if(/comment/.test(type))return 'insert';
        if(type==='variable'&&/^(br|rb|fr|rf|[rubf])$/i.test(token.string)&&token.end===pos.ch)return 'pair';
        if(/string/.test(type)||token.state.tokenize?.isString){
          let opening=token.string.match(/^(?:br|rb|fr|rf|[rubf])?('''|"""|'|")/i);
          if(!opening&&token.state.tokenize?.isString){
            opening=editor.getLineTokens(pos.line,true).filter(t=>t.start<pos.ch&&/string/.test(t.type||''))
              .map(t=>t.string.match(/^(?:br|rb|fr|rf|[rubf])?('''|"""|'|")/i)).filter(Boolean).at(-1);
          }
          const delimiter=opening?.[1]||token.string.match(/('''|"""|'|")$/)?.[1];
          const end=delimiter?token.string.length-delimiter.length:-1;
          const escapedEnd=(token.string.slice(0,end).match(/\\+$/)?.[0].length||0)%2;
          const closed=delimiter&&end>=(opening?.[0].length||0)&&token.string.endsWith(delimiter)&&!escapedEnd;
          if(token.end>pos.ch||token.state.tokenize?.isString||!closed)return line[pos.ch]===quote&&delimiter?.[0]===quote?'skip':'insert';
        }
        return null;
      });
      if(actions.some(action=>action===null))return CodeMirror.Pass;
      editor.operation(()=>{
        editor.replaceSelections(actions.map(action=>action==='pair'?quote+quote:action==='insert'?quote:''),'end','+input');
        editor.setSelections(editor.listSelections().map((range,index)=>{
          const pos=range.head;
          const direction=actions[index]==='skip'?1:actions[index]==='pair'?-1:0;
          const head=CodeMirror.Pos(pos.line,pos.ch+direction);
          return {anchor:head,head};
        }));
      });
    };
  }
  cm.addKeyMap({"'\"'":quoteKey('"'),"'''":quoteKey("'")});
}
