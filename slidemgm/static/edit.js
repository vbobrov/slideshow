function draw_image(canvas_id) {
	var canvas=$("#"+canvas_id);
	var canvas_height=canvas.height()
	var canvas_width=canvas.width()
	var image=$("#"+canvas.data("id"));
	var image_width=image.width()
	var image_height=image.height()
	var lcrop_px=parseInt(image_width*image.data("lcrop")/100);
	var tcrop_px=parseInt(image_height*image.data("tcrop")/100);
	var rcrop_px=parseInt(image_width*image.data("rcrop")/100);
	var bcrop_px=parseInt(image_height*image.data("bcrop")/100);
	var crop_width=rcrop_px-lcrop_px
	var crop_height=bcrop_px-tcrop_px
	var resize_ratio=Math.min(canvas_width/crop_width,canvas_height/crop_height)
	var draw_width=parseInt(crop_width*resize_ratio)
	var draw_height=parseInt(crop_height*resize_ratio)
	var context=canvas[0].getContext("2d");
	context.fillStyle="black"
	context.fillRect(0,0,canvas_width,canvas_height)
	context.drawImage(image[0],lcrop_px,tcrop_px,crop_width,crop_height,
							   parseInt((canvas_width-draw_width)/2),parseInt((canvas_height-draw_height)/2),draw_width,draw_height);
}

var croppers=new Object()

$(window).on("load",function() {
	$('canvas[id^="crop"]').each(function(i,val) {
		draw_image(val.id);
	})
	$('img').each(function() {
		$(this).on("click",function() {
			var image_id=$(this).attr("id");
			 var image=$("#"+image_id);
			var image_width=image.width()
			var image_height=image.height()
			var location=image.data("location")
			$("#imgsave"+image_id).prop("disabled",false)
			$("#imgcancel"+image_id).prop("disabled",false)
			$("#imgaspect"+image_id).prop("disabled",false)
			$("#location"+image_id).prop("disabled",false)
			crop_x=Math.round(image_width*image.data("lcrop")/100)
			crop_y=Math.round(image_height*image.data("tcrop")/100),
			crop_width=Math.round(image_width*(image.data("rcrop")-image.data("lcrop"))/100),
			crop_height=Math.round(image_height*(image.data("bcrop")-image.data("tcrop"))/100)
			console.log({
					x: crop_x,
					y: crop_y,
					width: crop_width,
					height: crop_height,
					aspect_ratio: (crop_width/crop_height).toFixed(2)
				}
			)
			if(Math.abs((crop_width/crop_height).toFixed(2)-3/4)<0.03) {
				$("#imgaspect"+image_id).prop("checked",true)
				var aspect_ratio=3/4
			} else {
				$("#imgaspect"+image_id).prop("checked",false)
				var aspect_ratio=NaN
			}
			 croppers[image_id] = new Cropper(image[0], {
				aspectRatio: aspect_ratio,
				viewMode: 2,
				modal: false,
				movable: false,
				rotatable: false,
				scalable: false,
				zoomable: false,
				data: {
					x: crop_x,
					y: crop_y,
					width: crop_width,
					height: crop_height
				}
			});
			$("#location"+image_id).val(location)
			$("#cropctl"+image_id).show();
		});
	});
	$('button[id^="img"]').each(function() {
		$(this).on("click",function () {
			var button_id=$(this).attr("id")
			var image_id=$(this).data("id")
			$("#imgsave"+image_id).prop("disabled",true)
			$("#imgcancel"+image_id).prop("disabled",true)
			$("#imgaspect"+image_id).prop("disabled",true)
			$("#location"+image_id).prop("disabled",true)
			//croppers[image_id].destroy()
			if(button_id.includes("save")) {
				var crop=croppers[image_id].getData(true)
				var image_info=croppers[image_id].getImageData()
				var image=$("#"+image_id)
				var image_width=image_info.naturalWidth
				var image_height=image_info.naturalHeight
				console.log(crop,image_width,image_height)
				var lcrop=Math.round(crop.x/image_width*100)
				var tcrop=Math.round(crop.y/image_height*100)
				var rcrop=Math.round((crop.x+crop.width)/image_width*100)
				var bcrop=Math.round((crop.y+crop.height)/image_height*100)
				$.ajax({
					type: "POST",
					contentType: "application/json",
					url: "/update/"+image_id,
					data: JSON.stringify({
						lcrop: lcrop,
						tcrop: tcrop,
						rcrop: rcrop,
						bcrop: bcrop,
						location: $("#location"+image_id).val()
					}),
					success: function(response) {
						var image_id=/.*\/(\d+)$/.exec(this.url)[1]
						croppers[image_id].destroy()
						var image=$("#"+image_id)
						image.data("lcrop",response.lcrop)
						image.data("tcrop",response.tcrop)
						image.data("rcrop",response.rcrop)
						image.data("bcrop",response.bcrop)
						image.data("location",response.location)
						draw_image("crop"+image_id)
						$("#cropctl"+image_id).hide()
						$("#"+image_id).closest("tr").removeClass()
						$("#"+image_id).closest("tr").addClass("bg-success")
						$("#info"+image_id).html("Location: "+response.location+"<br>Crops: "+response.lcrop+","+response.tcrop+","+response.rcrop+","+response.bcrop)
						setTimeout(function() {
							$("#"+image_id).closest("tr").removeClass()
						},2000)
					},
					error: function() {
						image_id=/.*\/(\d+)$/.exec(this.url)[1]
						console.log("In error",this.url,image_id)
						$("#"+image_id).closest("tr").addClass("bg-danger")
						$("#imgsave"+image_id).prop("disabled",false)
						$("#imgcancel"+image_id).prop("disabled",false)
						$("#imgaspect"+image_id).prop("disabled",false)
						$("#location"+image_id).prop("disabled",false)							
					}
				})
			} else {
				croppers[image_id].destroy()
				$("#cropctl"+image_id).hide()
				$("#"+image_id).closest("tr").removeClass()
			}
		})
	});
	$('input[id^=imgaspect]').each(function() {
		$(this).on("change",function() {
			croppers[$(this).data("id")].setAspectRatio($(this).prop("checked")?3/4:NaN)
		})
	});
});


