extends Control

var color_file :String = '' 
@onready var mesure_scene := preload("res://mesure.tscn")

# Called when the node enters the scene tree for the first time.
func _ready():
	pass # Replace with function body.


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta):
	pass


func _on_button_pressed():
	$FileDialog.show()


func _on_file_dialog_file_selected(path):
	color_file = path
	read_color_data()

func _on_mesure_selected(mesure_node) :
	%Couleur_preview.color = mesure_node.color_data
	print('mesure_seleced : ',mesure_node)
	%Couleur_label.text = ('Heure : ' + str(mesure_node.time_data[0]) +'h'+ str(mesure_node.time_data[1])
						  +'\nTemperature :' + str(mesure_node.temp_data) + 'K' 
						  +'\nR: ' + str(mesure_node.color_data.r)
						  +' G: ' + str(mesure_node.color_data.g)
						  +' B: ' + str(mesure_node.color_data.b)
						  +'\n HTML hexa : ' + mesure_node.color_data.to_html(false)
						  +'\n S: ' + str(mesure_node.SML_data.x)
						  +' M: ' + str(mesure_node.SML_data.y)
						  +' L: ' + str(mesure_node.SML_data.z))
func read_color_data() :
	var file_content = FileAccess.open(color_file,FileAccess.READ).get_as_text()
	file_content = file_content.split("\n")
	for mesure_txt in file_content :
		print(mesure_txt)
		var new_mesure_entry = mesure_scene.instantiate()
		new_mesure_entry._initialiser(mesure_txt)
		new_mesure_entry.connect('selected',_on_mesure_selected)
		%Tables_mesures.add_child(new_mesure_entry)
	
