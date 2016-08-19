
//function light_switch_control(light_switch){
//	var light_switch = $(light_switch);
//	var light_bulb = $("#light_bulb_" + light_switch.attr("light_switch_id"));
//	
//	if(light_bulb.hasClass("off")){									// when the light bulb has the class "off" do following:
//		light_bulb.removeClass("off");									// first remove the class "off"
//		light_switch.css("backgroundPosition","0 0");					// change the background position of the CSS sprite
//		light_bulb.stop().fadeTo(750,1);								// fade in the inner light bulb container (light is turned on!)
//	}else{															// else do following:
//		light_bulb.addClass("off");										// adding the class "off"
//		light_switch.css("backgroundPosition","-80px 0");				// move the background position of the switch back to original position
//		light_bulb.stop().fadeTo(750,0);								// fade out the turned on light (no more lights now)
//	}
//	
//}