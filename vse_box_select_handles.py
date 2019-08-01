# Add-on meta data
bl_info = {
    "name": "Box Select Strip Handles",
    "description": "Box selection operator that allows selection of single handlers",
    "author": "Salatfreak",
    "version": (0, 2),
    "blender": (2, 80, 0),
    "location": "Video Sequence Editor",
    "wiki_url": "https://github.com/Salatfreak/VSEBoxSelectHandles",
    "tracker_url": "https://github.com/Salatfreak/VSEBoxSelectHandles/issues",
    "category": "Sequencer",
}

# Import modules
import bpy

# Box select handles operator
class BoxSelectHandlesOperator(bpy.types.Operator):
    bl_idname = "sequencer.box_select_handles"
    bl_label = "Box Select Handles"
    
    # Operator properties
    wait_for_input: bpy.props.BoolProperty(name="Wait for Input", default=True)
    extend: bpy.props.BoolProperty(
        name="Extend", description="Extend the selection", default=False
    )

    # Only show for sequencer
    @classmethod
    def poll(cls, context):
        # Only show if box select works
        return bpy.ops.sequencer.select_box.poll()
    
    # Start modal execution
    def invoke(self, context, event):
        # Get mouse button roles
        keyconfig = context.window_manager.keyconfigs.active
        self._select_mouse = getattr(keyconfig.preferences, 'select_mouse', 'LEFT') + 'MOUSE'
        other_mouse = 'RIGHTMOUSE' if self._select_mouse == 'LEFTMOUSE' else 'LEFTMOUSE'
            
        # Cancel if invoked by wrong mouse button
        if event.type == other_mouse: return {'CANCELLED', 'PASS_THROUGH'}
    
        # Get view
        view = context.area.regions[3].view2d
        
        # Start with requested state
        if self.wait_for_input:
            self._state = 'WAIT'
        else:
            self._state = 'DRAG'
            if not self.extend: bpy.ops.sequencer.select_all(action='DESELECT')
            self._mouse_start = view.region_to_view(event.mouse_region_x, event.mouse_region_y)
        
        # Start modal execution
        bpy.ops.sequencer.view_ghost_border('INVOKE_DEFAULT', wait_for_input=self.wait_for_input)
        context.window_manager.modal_handler_add(self)
        self._select = True
        return {'RUNNING_MODAL'}
    
    # Handle modal events
    def modal(self, context, event):
        # Get view
        view = context.area.regions[3].view2d
        
        # Get mouse button to handle
        mouse_button = 'LEFTMOUSE' if self.wait_for_input else self._select_mouse
        
        # Handle inputs
        if self._state in {'FINISHED', 'CANCELLED'}: return {self._state}
        if event.type == mouse_button:
            if self._state == 'WAIT' and not event.ctrl:
                if event.value == 'PRESS':
                    if not self.extend: bpy.ops.sequencer.select_all(action='DESELECT')
                    self._mouse_start = view.region_to_view(event.mouse_region_x, event.mouse_region_y)
                    self._state = 'DRAG'
            if event.value == 'RELEASE':
                if self._state == 'DRAG':
                    self._mouse_end = view.region_to_view(event.mouse_region_x, event.mouse_region_y)
                    if event.shift: self._select = False
                    self.execute(context)
                    self._state = 'FINISHED'
                else:
                    self._state = 'CANCELLED'
        elif event.value == 'PRESS' and event.type in {'RIGHTMOUSE', 'ESC'}:
            self._state = 'CANCELLED'
        return {'PASS_THROUGH'}
    
    # Make selection
    def execute(self, context):
        # Get border
        min_c = round(min(self._mouse_start[1], self._mouse_end[1]))
        max_c = round(max(self._mouse_start[1], self._mouse_end[1])) - 1
        min_f = min(self._mouse_start[0], self._mouse_end[0])
        max_f = max(self._mouse_start[0], self._mouse_end[0])
        
        # Select or deselect handles
        for s in context.sequences:
            # Skip if not in channel
            if not (min_c <= s.channel and s.channel <= max_c): continue
            
            # Apply to handles if in frame range
            apply_left = (
                min_f < s.frame_final_start and s.frame_final_start < max_f
            )
            apply_right = (
                min_f < s.frame_final_end and s.frame_final_end < max_f
            )
                
            # Set selected
            if apply_left or apply_right:
                # Transfer regular selection to handles
                if s.select \
                and not s.select_left_handle and not s.select_right_handle:
                    s.select_left_handle = s.select_right_handle = True
                    
                # Apply selection
                if apply_left: s.select_left_handle = self._select
                if apply_right: s.select_right_handle = self._select
                
                # Transfer to regular selection if both selected
                if s.select_left_handle and s.select_right_handle:
                    s.select = True
                    s.select_left_handle = s.select_right_handle = False
                # Select if one selected
                elif s.select_left_handle or s.select_right_handle:
                    s.select = True
                # Deselect else
                else:
                    s.select = False
                
        # Return sucessfully
        return {'FINISHED'}

# Register add-on
keymap = None
def register():
    global keymap
    
    # Register operator
    bpy.utils.register_class(BoxSelectHandlesOperator)
    
    # Create keymap for left and right mouse button to be able to react
    # whether the "Select With" preference is set to right or left
    keymap = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
        name='Sequencer', space_type='SEQUENCE_EDITOR'
    )
    kmi = keymap.keymap_items.new(
        BoxSelectHandlesOperator.bl_idname, 'LEFTMOUSE', 'PRESS', ctrl=True
    )
    kmi.properties.wait_for_input = False
    kmi.properties.extend = False
    kmi = keymap.keymap_items.new(
        BoxSelectHandlesOperator.bl_idname, 'RIGHTMOUSE', 'PRESS', ctrl=True
    )
    kmi.properties.wait_for_input = False
    kmi.properties.extend = False
    kmi = keymap.keymap_items.new(
        BoxSelectHandlesOperator.bl_idname, 'B', 'PRESS', ctrl=True
    )
    kmi.properties.wait_for_input = True
    kmi.properties.extend = True
    

# Unregister add-on
def unregister():
    # Remove keymap
    for item in keymap.keymap_items: keymap.keymap_items.remove(item)
    keymap = None
    
    # Unegister operator
    bpy.utils.unregister_class(BoxSelectHandlesOperator)
    
# Register on script execution
if __name__ == '__main__':
    register()