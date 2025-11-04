#!/usr/bin/env python3
"""
DWG/DXF to JSON Converter using ezdxf
"""

import json
import os

import tempfile
from typing import TYPE_CHECKING, Any, Dict

from fastapi import HTTPException, UploadFile

try:  # pragma: no cover - dependency availability is runtime-specific
    import ezdxf  # type: ignore
except ImportError:  # pragma: no cover - handled at runtime
    ezdxf = None  # type: ignore[assignment]


if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from ezdxf.document import Drawing  # type: ignore
    from ezdxf.entities import DXFEntity  # type: ignore


def extract_entity_data(entity):
    """Extract relevant data from an entity"""
    data = {
        'type': entity.dxftype(),
        'layer': entity.dxf.layer if hasattr(entity.dxf, 'layer') else None,
    }
    
    # Extract color
    if hasattr(entity.dxf, 'color'):
        data['color'] = entity.dxf.color
    
    # Extract geometry based on type
    if entity.dxftype() == 'LINE':
        data['start'] = [entity.dxf.start.x, entity.dxf.start.y, entity.dxf.start.z]
        data['end'] = [entity.dxf.end.x, entity.dxf.end.y, entity.dxf.end.z]
    
    elif entity.dxftype() == 'CIRCLE':
        data['center'] = [entity.dxf.center.x, entity.dxf.center.y, entity.dxf.center.z]
        data['radius'] = entity.dxf.radius
    
    elif entity.dxftype() == 'ARC':
        data['center'] = [entity.dxf.center.x, entity.dxf.center.y, entity.dxf.center.z]
        data['radius'] = entity.dxf.radius
        data['start_angle'] = entity.dxf.start_angle
        data['end_angle'] = entity.dxf.end_angle
    
    elif entity.dxftype() == 'LWPOLYLINE':
        points = []
        for point in entity.get_points('xy'):
            points.append([point[0], point[1]])
        data['points'] = points
        data['closed'] = entity.closed
    
    elif entity.dxftype() == 'POLYLINE':
        points = []
        for vertex in entity.vertices:
            points.append([vertex.dxf.location.x, vertex.dxf.location.y, vertex.dxf.location.z])
        data['points'] = points
        data['closed'] = entity.is_closed
    
    elif entity.dxftype() == 'TEXT':
        data['text'] = entity.dxf.text if hasattr(entity.dxf, 'text') else ''
        data['insert'] = [entity.dxf.insert.x, entity.dxf.insert.y, entity.dxf.insert.z]
        data['height'] = entity.dxf.height if hasattr(entity.dxf, 'height') else None
    
    elif entity.dxftype() == 'MTEXT':
        data['text'] = entity.text
        data['insert'] = [entity.dxf.insert.x, entity.dxf.insert.y, entity.dxf.insert.z]
    
    elif entity.dxftype() == 'INSERT':
        data['name'] = entity.dxf.name
        data['insert'] = [entity.dxf.insert.x, entity.dxf.insert.y, entity.dxf.insert.z]
        if hasattr(entity.dxf, 'xscale'):
            data['scale'] = [entity.dxf.xscale, entity.dxf.yscale, entity.dxf.zscale]
    
    elif entity.dxftype() == 'DIMENSION':
        data['dimension_type'] = entity.dimtype
        data['defpoint'] = [entity.dxf.defpoint.x, entity.dxf.defpoint.y, entity.dxf.defpoint.z]
    
    return data

def convert_dwg_to_json(input_file, output_file=None):
    """Convert DWG/DXF to JSON"""
    import ezdxf
    
    print(f"🔄 Reading file: {input_file}")
    
    try:
        # Try to read as DXF first, then DWG
        if input_file.lower().endswith('.dxf'):
            doc = ezdxf.readfile(input_file)
        elif input_file.lower().endswith('.dwg'):
            print("📖 Attempting to read DWG file...")
            try:
                doc = ezdxf.readfile(input_file)
            except Exception as e:
                print(f"⚠️  Direct DWG reading failed: {e}")
                print("\n💡 DWG files need to be converted to DXF first.")
                print("   Options:")
                print("   1. Use AutoCAD, LibreCAD, or FreeCAD to export as DXF")
                print("   2. Use online converter: https://www.zamzar.com/")
                print("   3. Download ODA File Converter (free)")
                return None
        else:
            print("❌ Unsupported file format. Use .dwg or .dxf")
            return None
        
        # Extract data
        result = {
            'filename': os.path.basename(input_file),
            'version': doc.dxfversion,
            'layers': {},
            'entities': [],
            'blocks': {},
            'statistics': {
                'total_entities': 0,
                'entities_by_type': {},
                'total_layers': 0,
                'total_blocks': 0
            }
        }
        
        # Get layers
        print("📊 Extracting layers...")
        for layer in doc.layers:
            result['layers'][layer.dxf.name] = {
                'name': layer.dxf.name,
                'color': layer.dxf.color if hasattr(layer.dxf, 'color') else None,
                'linetype': layer.dxf.linetype if hasattr(layer.dxf, 'linetype') else None,
            }
        result['statistics']['total_layers'] = len(result['layers'])
        
        # Get entities from modelspace
        print("📐 Extracting entities...")
        msp = doc.modelspace()
        for entity in msp:
            entity_data = extract_entity_data(entity)
            result['entities'].append(entity_data)
            
            # Update statistics
            entity_type = entity.dxftype()
            if entity_type not in result['statistics']['entities_by_type']:
                result['statistics']['entities_by_type'][entity_type] = 0
            result['statistics']['entities_by_type'][entity_type] += 1
        
        result['statistics']['total_entities'] = len(result['entities'])
        
        # Get blocks
        print("🧱 Extracting blocks...")
        for block in doc.blocks:
            if not block.name.startswith('*'):  # Skip anonymous blocks
                block_entities = []
                for entity in block:
                    block_entities.append(extract_entity_data(entity))
                result['blocks'][block.name] = {
                    'name': block.name,
                    'entities': block_entities
                }
        result['statistics']['total_blocks'] = len(result['blocks'])
        
        # Write to JSON
        if output_file is None:
            output_file = os.path.splitext(input_file)[0] + '.json'
        
        print(f"💾 Writing to: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print("\n✅ Conversion complete!")
        print(f"\n📊 Summary:")
        print(f"   Version: {result['version']}")
        print(f"   Layers: {result['statistics']['total_layers']}")
        print(f"   Entities: {result['statistics']['total_entities']}")
        print(f"   Blocks: {result['statistics']['total_blocks']}")
        print(f"\n📈 Entities by type:")
        for entity_type, count in sorted(result['statistics']['entities_by_type'].items()):
            print(f"   {entity_type}: {count}")
        
        return result

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

async def convert_dxf_upload_to_json(dxf_file: UploadFile) -> Dict[str, Any]:

    input_file = dxf_file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_output:
        output_file = temp_output.name

    return convert_dwg_to_json(input_file, output_file)

__all__ = ["convert_dxf_upload_to_json"]
