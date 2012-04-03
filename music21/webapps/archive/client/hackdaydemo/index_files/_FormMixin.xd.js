/*
	Copyright (c) 2004-2009, The Dojo Foundation All Rights Reserved.
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	see: http://dojotoolkit.org/license for details
*/


window[(typeof (djConfig)!="undefined"&&djConfig.scopeMap&&djConfig.scopeMap[0][1])||"dojo"]._xdResourceLoaded(function(_1,_2,_3){return {depends:[["provide","dijit.form._FormMixin"]],defineResource:function(_4,_5,_6){if(!_4._hasResource["dijit.form._FormMixin"]){_4._hasResource["dijit.form._FormMixin"]=true;_4.provide("dijit.form._FormMixin");_4.declare("dijit.form._FormMixin",null,{reset:function(){_4.forEach(this.getDescendants(),function(_7){if(_7.reset){_7.reset();}});},validate:function(){var _8=false;return _4.every(_4.map(this.getDescendants(),function(_9){_9._hasBeenBlurred=true;var _a=_9.disabled||!_9.validate||_9.validate();if(!_a&&!_8){_5.scrollIntoView(_9.containerNode||_9.domNode);_9.focus();_8=true;}return _a;}),function(_b){return _b;});},setValues:function(_c){_4.deprecated(this.declaredClass+"::setValues() is deprecated. Use attr('value', val) instead.","","2.0");return this.attr("value",_c);},_setValueAttr:function(_d){var _e={};_4.forEach(this.getDescendants(),function(_f){if(!_f.name){return;}var _10=_e[_f.name]||(_e[_f.name]=[]);_10.push(_f);});for(var _11 in _e){if(!_e.hasOwnProperty(_11)){continue;}var _12=_e[_11],_13=_4.getObject(_11,false,_d);if(_13===undefined){continue;}if(!_4.isArray(_13)){_13=[_13];}if(typeof _12[0].checked=="boolean"){_4.forEach(_12,function(w,i){w.attr("value",_4.indexOf(_13,w.value)!=-1);});}else{if(_12[0].multiple){_12[0].attr("value",_13);}else{_4.forEach(_12,function(w,i){w.attr("value",_13[i]);});}}}},getValues:function(){_4.deprecated(this.declaredClass+"::getValues() is deprecated. Use attr('value') instead.","","2.0");return this.attr("value");},_getValueAttr:function(){var obj={};_4.forEach(this.getDescendants(),function(_14){var _15=_14.name;if(!_15||_14.disabled){return;}var _16=_14.attr("value");if(typeof _14.checked=="boolean"){if(/Radio/.test(_14.declaredClass)){if(_16!==false){_4.setObject(_15,_16,obj);}else{_16=_4.getObject(_15,false,obj);if(_16===undefined){_4.setObject(_15,null,obj);}}}else{var ary=_4.getObject(_15,false,obj);if(!ary){ary=[];_4.setObject(_15,ary,obj);}if(_16!==false){ary.push(_16);}}}else{var _17=_4.getObject(_15,false,obj);if(typeof _17!="undefined"){if(_4.isArray(_17)){_17.push(_16);}else{_4.setObject(_15,[_17,_16],obj);}}else{_4.setObject(_15,_16,obj);}}});return obj;},isValid:function(){this._invalidWidgets=_4.filter(this.getDescendants(),function(_18){return !_18.disabled&&_18.isValid&&!_18.isValid();});return !this._invalidWidgets.length;},onValidStateChange:function(_19){},_widgetChange:function(_1a){var _1b=this._lastValidState;if(!_1a||this._lastValidState===undefined){_1b=this.isValid();if(this._lastValidState===undefined){this._lastValidState=_1b;}}else{if(_1a.isValid){this._invalidWidgets=_4.filter(this._invalidWidgets||[],function(w){return (w!=_1a);},this);if(!_1a.isValid()&&!_1a.attr("disabled")){this._invalidWidgets.push(_1a);}_1b=(this._invalidWidgets.length===0);}}if(_1b!==this._lastValidState){this._lastValidState=_1b;this.onValidStateChange(_1b);}},connectChildren:function(){_4.forEach(this._changeConnections,_4.hitch(this,"disconnect"));var _1c=this;var _1d=this._changeConnections=[];_4.forEach(_4.filter(this.getDescendants(),function(_1e){return _1e.validate;}),function(_1f){_1d.push(_1c.connect(_1f,"validate",_4.hitch(_1c,"_widgetChange",_1f)));_1d.push(_1c.connect(_1f,"_setDisabledAttr",_4.hitch(_1c,"_widgetChange",_1f)));});this._widgetChange(null);},startup:function(){this.inherited(arguments);this._changeConnections=[];this.connectChildren();}});}}};});