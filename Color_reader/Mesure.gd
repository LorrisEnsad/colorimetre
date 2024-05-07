extends Control

#Exemple de texte d'entrée 
#19h0  R: 0.1215624 | G: 0.1659142 | B: 0.1443062||     X: 0.03298611 | Y: 0.0150525 | Z: 0.1443062||     Temperature : 0

var text_data :String : set = _initialiser
var color_data :Color
var temp_data :float
var XYZ_data :Vector3
var SML_data :Vector3
var time_data :Vector2
# Called when the node enters the scene tree for the first time.

signal selected(self_node)

func _ready():
	pass



func _initialiser(text :String) :
	if text != '' :
		text_data = text
		var parsed :PackedStringArray = text.split('||')
		var time_RGB_txt = parsed[0].split(' ')

		
		time_data.x = float(time_RGB_txt[0].split('h')[0])
		time_data.y = float(time_RGB_txt[0].split('h')[1])
		print(time_data)
		%Label.text = str(time_data.x)+'h'+str(time_data.y)
		
		color_data.r = float(time_RGB_txt[3])
		color_data.g = float(time_RGB_txt[6])
		color_data.b = float(time_RGB_txt[9])
		print(color_data)
		%ColorRect.color = color_data
		
		XYZ_data.x = float(parsed[1].split(' ')[6])
		XYZ_data.y = float(parsed[1].split(' ')[8])
		XYZ_data.z = float(parsed[1].split(' ')[11])
		print(XYZ_data)
		
		SML_data.x = float(parsed[3].split(' ')[1])
		SML_data.y = float(parsed[3].split(' ')[3])
		SML_data.z = float(parsed[3].split(' ')[5])
		print(SML_data)
		
		temp_data = float(parsed[2].split(' ')[7])
		print(temp_data)
	else :
		queue_free()
	
	
	
	

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta):
	pass


func _on_button_pressed():
	selected.emit(self)
