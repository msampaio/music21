/*
	Copyright (c) 2004-2009, The Dojo Foundation All Rights Reserved.
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	see: http://dojotoolkit.org/license for details
*/


window[(typeof (djConfig)!="undefined"&&djConfig.scopeMap&&djConfig.scopeMap[0][1])||"dojo"]._xdResourceLoaded(function(_1,_2,_3){return {depends:[["provide","dijit._Container"]],defineResource:function(_4,_5,_6){if(!_4._hasResource["dijit._Container"]){_4._hasResource["dijit._Container"]=true;_4.provide("dijit._Container");_4.declare("dijit._Container",null,{isContainer:true,buildRendering:function(){this.inherited(arguments);if(!this.containerNode){this.containerNode=this.domNode;}},addChild:function(_7,_8){var _9=this.containerNode;if(_8&&typeof _8=="number"){var _a=this.getChildren();if(_a&&_a.length>=_8){_9=_a[_8-1].domNode;_8="after";}}_4.place(_7.domNode,_9,_8);if(this._started&&!_7._started){_7.startup();}},removeChild:function(_b){if(typeof _b=="number"&&_b>0){_b=this.getChildren()[_b];}if(_b&&_b.domNode){var _c=_b.domNode;_c.parentNode.removeChild(_c);}},getChildren:function(){return _4.query("> [widgetId]",this.containerNode).map(_5.byNode);},hasChildren:function(){return _4.query("> [widgetId]",this.containerNode).length>0;},destroyDescendants:function(_d){_4.forEach(this.getChildren(),function(_e){_e.destroyRecursive(_d);});},_getSiblingOfChild:function(_f,dir){var _10=_f.domNode,_11=(dir>0?"nextSibling":"previousSibling");do{_10=_10[_11];}while(_10&&(_10.nodeType!=1||!_5.byNode(_10)));return _10&&_5.byNode(_10);},getIndexOfChild:function(_12){return _4.indexOf(this.getChildren(),_12);},startup:function(){if(this._started){return;}_4.forEach(this.getChildren(),function(_13){_13.startup();});this.inherited(arguments);}});}}};});