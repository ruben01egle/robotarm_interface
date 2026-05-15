import os
import re

# --- Konfiguration ---
MSG_DIR = "./src/interface/msg"
OUTPUT_DIR = "./include/protocol"
MAGIC_BYTE = 0xAA

DEBUG_MODE = False

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

TYPE_SIZES = {
    'uint8_t': '1',
    'uint16_t': '2',
    'uint32_t': '4',
    'int32_t': '4',
    'float': '4',
    'double': '8',
    'bool': '1',
    'RosTimestamp': '8'
}

def create_common_header():
    content = f"""#pragma once
#include <cstdint>
#include <cstring>

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
    
    with open(filepath, 'rb') as f:
        content_bytes = f.read()
    content_str = content_bytes.decode('utf-8', errors='ignore')

    if content_str and not content_str.endswith('\n') and not content_str.endswith('\r'):
        content_str += '\n'
        
    lines = re.split(r'\r\n|\n|\r', content_str)
    
    for line in lines:
        line_clean = line.split('#')[0].strip()
        if not line_clean: 
            continue
        
        if '=' in line_clean and '<=' not in line_clean and '>=' not in line_clean:
            match = re.match(r'(\S+)\s+(\S+)\s*=\s*(\S+)', line_clean)
            if match:
                constants.append((match.group(1), match.group(2), match.group(3)))
                continue 

        parts = line_clean.split()
        if len(parts) >= 2:
            ros_full_type = parts[0].strip()
            field_name = parts[1].strip()
            
            array_match = re.search(r'([^\[\]]+)\[(<=)?(\d*)\]', ros_full_type)
            
            if array_match:
                base_type = array_match.group(1).split('/')[-1].strip()
                is_variable = array_match.group(2) == "<="
                size = array_match.group(3).strip()
                
                cpp_type = TYPE_MAPPING.get(base_type, base_type)
                
                if is_variable:
                    fields.append(("uint32_t", f"{field_name}_count", False, False, 0, "", False))
                    fields.append((cpp_type, f"{field_name}", True, True, int(size if size else 1), f"{field_name}_count", True))
                else:
                    fields.append((cpp_type, f"{field_name}", True, False, int(size if size else 1), "", False))
            else:
                base_type = ros_full_type.split('/')[-1].strip()
                cpp_type = TYPE_MAPPING.get(base_type, base_type)
                fields.append((cpp_type, field_name, False, False, 0, "", False))
                
    return fields, constants

def generate_hpp(msg_name, fields, constants):
    includes = set()
    known_primitives = set(TYPE_MAPPING.values()) | {
        "uint8_t", "uint16_t", "uint32_t", "int32_t", "float", "double", "bool"
    }

    has_variable_array = False
    for f_type, _, _, is_variable, _, _, _ in fields:
        if f_type not in known_primitives:
            includes.add(f"#include \"{f_type}.hpp\"")
        if is_variable:
            has_variable_array = True

    include_str = "\n".join(sorted(list(includes)))
    if include_str:
        include_str = "\n" + include_str

    size_expr_parts = []
    serialize_parts = []
    sequential_deserialize_parts = []
    array_max_size_constants = []

    # Mapping, um schnell herauszufinden, welcher Counter zu welchem Array gehört
    counter_to_max_size = {}
    for _, f_name, is_array, is_variable, max_size, counter_name, _ in fields:
        if is_array and is_variable:
            counter_to_max_size[counter_name] = (f"MAX_{f_name.upper()}_SIZE", max_size)

    for f_type, f_name, is_array, is_variable, max_size, counter_name, _ in fields:
        if f_type in TYPE_SIZES:
            element_size = TYPE_SIZES[f_type]
        else:
            element_size = f"sizeof({f_type})"

        # --- SERIALIZE GENERIERUNG (SLOW PATH) ---
        if is_array:
            if is_variable:
                size_expr_parts.append(f"({counter_name} * {element_size})")
                if f_type in TYPE_SIZES:
                    serialize_parts.append(f"        std::memcpy(dest + offset, {f_name}, {counter_name} * {element_size});\n        offset += {counter_name} * {element_size};")
                else:
                    serialize_parts.append(f"        for(uint32_t i = 0; i < {counter_name}; ++i) {{\n            std::memcpy(dest + offset, &{f_name}[i], sizeof({f_type}));\n            offset += sizeof({f_type});\n        }}")
            else:
                size_expr_parts.append(f"({max_size} * {element_size})")
                serialize_parts.append(f"        std::memcpy(dest + offset, {f_name}, {max_size} * {element_size});\n        offset += {max_size} * {element_size};")
        else:
            size_expr_parts.append(f"sizeof({f_type})")
            serialize_parts.append(f"        std::memcpy(dest + offset, &{f_name}, sizeof({f_type}));\n        offset += sizeof({f_type});")

        # --- DESERIALIZE GENERIERUNG (SLOW PATH - STRIKT SEQUENTIELL) ---
        if is_array:
            if is_variable:
                if f_type in TYPE_SIZES:
                    sequential_deserialize_parts.append(f"        if (offset + {counter_name} * {element_size} > size) return false;\n        std::memcpy({f_name}, src + offset, {counter_name} * {element_size});\n        offset += {counter_name} * {element_size};")
                else:
                    sequential_deserialize_parts.append(f"        if (offset + {counter_name} * sizeof({f_type}) > size) return false;\n        for(uint32_t i = 0; i < {counter_name}; ++i) {{\n            std::memcpy(&{f_name}[i], src + offset, sizeof({f_type}));\n            offset += sizeof({f_type});\n        }}")
            else:
                sequential_deserialize_parts.append(f"        if (offset + {max_size} * {element_size} > size) return false;\n        std::memcpy({f_name}, src + offset, {max_size} * {element_size});\n        offset += {max_size} * {element_size};")
        else:
            # Primitiv-Feld einlesen
            sequential_deserialize_parts.append(f"        if (offset + sizeof({f_type}) > size) return false;\n        std::memcpy(&{f_name}, src + offset, sizeof({f_type}));\n        offset += sizeof({f_type});")
            
            # KORREKTUR: Wenn DIESES Primitiv-Feld ein Zähler für ein folgendes Array ist, JETZT SOFORT prüfen!
            if f_name in counter_to_max_size:
                const_macro_name, _ = counter_to_max_size[f_name]
                sequential_deserialize_parts.append(f"        if ({f_name} > {const_macro_name}) return false;")

    # Registriere die constexpr Definitionen für die Klassen-Kopfzeile
    for _, (const_macro_name, max_size) in counter_to_max_size.items():
        array_max_size_constants.append((const_macro_name, max_size))

    size_expression = " + ".join(size_expr_parts) if size_expr_parts else "0"
    serialize_body = "\n".join(serialize_parts)
    deserialize_body = "\n".join(sequential_deserialize_parts)

    if has_variable_array:
        fast_path_conditions = []
        for _, f_name, _, is_variable, _, counter_name, _ in fields:
            if is_variable:
                fast_path_conditions.append(f"{counter_name} == MAX_{f_name.upper()}_SIZE")

        fast_path_cond_str = " && ".join(fast_path_conditions)

        # Logik für get_serialized_size()
        smart_size_body = f"""        if ({fast_path_cond_str}) {{
            return sizeof({msg_name});
        }}
        return {size_expression};"""

        smart_serialize_body = f"""
        if ({fast_path_cond_str}) {{
            std::memcpy(dest, this, sizeof({msg_name}));
            return sizeof({msg_name});
        }}

        size_t offset = 0;
{serialize_body}
        return offset;"""

        smart_deserialize_body = f"""
        if (size == sizeof({msg_name})) {{
            std::memcpy(this, src, sizeof({msg_name}));
            return true;
        }}

        size_t offset = 0;
{deserialize_body}
        return true;"""
    else:
        smart_size_body = f"        return sizeof({msg_name});"
        
        smart_serialize_body = f"""        std::memcpy(dest, this, sizeof({msg_name}));
        return sizeof({msg_name});"""
        
        smart_deserialize_body = f"""        if (size != sizeof({msg_name})) return false;
        std::memcpy(this, src, sizeof({msg_name}));
        return true;"""
        

    content = f"""#pragma once
#include "ProtocolCommon.hpp"{include_str}
#include <cstddef>

#pragma pack(push, 1)
class {msg_name} {{
public:
"""
    if constants or array_max_size_constants:
        content += "    // Constants\n"
        for _, c_name, c_val in constants:
            content += f"    static constexpr uint32_t {c_name} = {c_val};\n"
        for const_macro_name, max_size in array_max_size_constants:
            content += f"    static constexpr uint32_t {const_macro_name} = {max_size};\n"
        content += "\n"

    content += "    // Message Fields\n"
    for f_type, f_name, is_array, _, max_size, _, _ in fields:
        if is_array:
            content += f"    {f_type} {f_name}[{max_size}];\n"
        else:
            content += f"    {f_type} {f_name};\n"

    content += f"""
    {msg_name}() = default;

    size_t get_serialized_size() const {{
{smart_size_body}
    }}

    size_t serialize(uint8_t* dest) const {{
{smart_serialize_body}
    }}

    bool deserialize(const uint8_t* src, size_t size) {{
{smart_deserialize_body}
    }}
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
    for filename in msg_files:
        msg_name = filename[:-4]
        fields, constants = parse_msg_file(os.path.join(MSG_DIR, filename))
        generate_hpp(msg_name, fields, constants)
    print(f"Generated headers in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()