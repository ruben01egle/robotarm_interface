import os
import re

# --- Konfiguration ---
MSG_DIR = "./src/interface/msg"
OUTPUT_DIR = "./include/protocol"
MAGIC_BYTE = 0xAA

# Setze auf False, um die ausführlichen Debug-Ausgaben zu deaktivieren
DEBUG_MODE = True

# Standard-Mapping für ROS-Primitivtypen
TYPE_MAPPING = {
    'uint8': 'uint8_t',
    'uint16': 'uint16_t',
    'uint32': 'uint32_t',
    'int32': 'int32_t',
    'float32': 'float',
    'float64': 'double',
    'bool': 'bool',
    'time': 'RosTimestamp'
}

def create_common_header():
    content = f"""#pragma once
#include <cstdint>

#pragma pack(push, 1)
struct RosTimestamp {{
    uint32_t sec;
    uint32_t nsec;
}};

struct PacketHeader {{
    uint8_t magic = {hex(MAGIC_BYTE)};
    uint8_t msg_type;
    uint32_t msg_id;
    uint32_t payload_size;
}};
#pragma pack(pop)
"""
    if not os.path.exists(OUTPUT_DIR): 
        os.makedirs(OUTPUT_DIR)
    with open(os.path.join(OUTPUT_DIR, "ProtocolCommon.hpp"), "w") as f:
        f.write(content)

def parse_msg_file(filepath):
    fields = []
    constants = []
    
    # Datei als Binary lesen, um EOF- und Zeilenumbruch-Probleme zu umgehen
    with open(filepath, 'rb') as f:
        content_bytes = f.read()
    content_str = content_bytes.decode('utf-8', errors='ignore')

    # Fehlenden finalen Zeilenumbruch absichern
    if content_str and not content_str.endswith('\n') and not content_str.endswith('\r'):
        content_str += '\n'
        
    lines = re.split(r'\r\n|\n|\r', content_str)
    
    if DEBUG_MODE:
        print(f"  [DEBUG] Verarbeite Datei mit {len(lines)} Zeilen-Slots...")

    for line in lines:
        # Kommentare abschneiden und Leerzeichen entfernen
        line_clean = line.split('#')[0].strip()
        if not line_clean: 
            continue
        
        # Konstanten-Check: Verhindert, dass Arrays wie [<=5] hier fälschlicherweise reinlaufen
        if '=' in line_clean and '<=' not in line_clean and '>=' not in line_clean:
            match = re.match(r'(\S+)\s+(\S+)\s*=\s*(\S+)', line_clean)
            if match:
                constants.append((match.group(1), match.group(2), match.group(3)))
                if DEBUG_MODE:
                    print(f"    -> Konstante gefunden: {match.group(2)} = {match.group(3)}")
                continue 

        # Feld-Check
        parts = line_clean.split()
        if len(parts) >= 2:
            ros_full_type = parts[0].strip()
            field_name = parts[1].strip()
            
            # Matcht Array-Typen wie TelemetryFrame[<=5] oder uint8[32]
            array_match = re.search(r'([^\[\]]+)\[(<=)?(\d*)\]', ros_full_type)
            
            if array_match:
                base_type = array_match.group(1).split('/')[-1].strip()
                is_variable = array_match.group(2) == "<="
                size = array_match.group(3).strip()
                
                cpp_type = TYPE_MAPPING.get(base_type, base_type)
                
                if is_variable:
                    fields.append(("uint32_t", f"{field_name}_count"))
                
                array_size = size if size else "1"
                fields.append((cpp_type, f"{field_name}[{array_size}]"))
                
                if DEBUG_MODE:
                    print(f"    -> Array extrahiert: {cpp_type} {field_name}[{array_size}]" + (" (+ Counter)" if is_variable else ""))
            else:
                # Normaler Primitiv- oder Custom-Typ
                base_type = ros_full_type.split('/')[-1].strip()
                cpp_type = TYPE_MAPPING.get(base_type, base_type)
                fields.append((cpp_type, field_name))
                
                if DEBUG_MODE:
                    print(f"    -> Feld extrahiert: {cpp_type} {field_name}")
                
    return fields, constants

def generate_hpp(msg_name, fields, constants):
    includes = set()
    
    # Primitivtypen filtern, damit dafür kein #include generiert wird
    known_primitives = set(TYPE_MAPPING.values()) | {
        "uint8_t", "uint16_t", "uint32_t", "int32_t", "float", "double", "bool"
    }

    for f_type, _ in fields:
        clean_type = f_type.split('[')[0].strip()
        if clean_type not in known_primitives:
            includes.add(f"#include \"{clean_type}.hpp\"")

    include_str = "\n".join(sorted(list(includes)))
    if include_str:
        include_str = "\n" + include_str

    content = f"""#pragma once
#include "ProtocolCommon.hpp"{include_str}

#pragma pack(push, 1)
class {msg_name} {{
public:
"""
    if constants:
        content += "    // Constants\n"
        for _, c_name, c_val in constants:
            content += f"    static constexpr uint32_t {c_name} = {c_val};\n"
        content += "\n"

    content += "    // Message Fields\n"
    for f_type, f_name in fields:
        content += f"    {f_type} {f_name};\n"

    content += f"""
    {msg_name}() = default;
}};
#pragma pack(pop)
"""
    
    out_path = os.path.join(OUTPUT_DIR, f"{msg_name}.hpp")
    with open(out_path, "w", encoding='utf-8') as f:
        f.write(content)

def main():
    if not os.path.exists(OUTPUT_DIR): 
        os.makedirs(OUTPUT_DIR)
        
    create_common_header()
    
    msg_files = [f for f in os.listdir(MSG_DIR) if f.endswith(".msg")]
    print(f"Starte Codegenerierung für {len(msg_files)} Dateien...")
    
    for filename in msg_files:
        msg_name = filename[:-4]
        print(f"Verarbeite: {filename}")
        fields, constants = parse_msg_file(os.path.join(MSG_DIR, filename))
        generate_hpp(msg_name, fields, constants)
        
    print(f"\nErfolgreich beendet! {len(msg_files)} Header-Dateien in '{OUTPUT_DIR}' erstellt.")

if __name__ == "__main__":
    main()