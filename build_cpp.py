import os
import re

# --- Konfiguration ---
MSG_DIR = "./src/interface/msg"
OUTPUT_DIR = "./include/protocol"
MAGIC_BYTE = 0x6666

DEBUG_MODE = False

TYPE_MAPPING = {
    'uint8': 'uint8_t',
    'uint16': 'uint16_t',
    'uint32': 'uint32_t',
    'int32': 'int32_t',
    'float32': 'float',
    'float64': 'double',
    'bool': 'bool',
    'time': 'RosTimestamp',
    'Time': 'RosTimestamp',
    'builtin_interfaces/Time': 'RosTimestamp'
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

def camel_to_snake(name):
    # Hilfsfunktion, um z.B. TrajectoryBatch zu TRAJECTORY_BATCH für das Enum umzuwandeln
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).upper()

def create_common_header(msg_names):
    # Generiere die Enum-Einträge dynamisch basierend auf den gefundenen Dateien
    enum_entries = ["    UNKNOWN = 0"]
    for i, msg_name in enumerate(sorted(msg_names), start=1):
        enum_name = camel_to_snake(msg_name)
        enum_entries.append(f"    {enum_name} = {i}")
    
    enum_str = ",\n".join(enum_entries)

    content = f"""#pragma once
#include <cstdint>
#include <cstring>

#pragma pack(push, 1)

constexpr uint32_t UDP_MAGIC = {hex(MAGIC_BYTE)};

// Automatically generated message types
enum class MessageType : uint32_t {{
{enum_str}
}};

struct RosTimestamp {{
    uint32_t sec;
    uint32_t nsec;
}};

struct PacketHeader {{
    uint32_t    magic = UDP_MAGIC;
    MessageType msg_type;
    uint32_t    msg_id;
    uint32_t    payload_size;
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
                base_type = ros_full_type
                if base_type not in TYPE_MAPPING:
                    base_type = array_match.group(1).split('/')[-1].strip()
                
                is_variable = array_match.group(2) == "<="
                size = array_match.group(3).strip()
                
                cpp_type = TYPE_MAPPING.get(base_type, base_type)
                
                if is_variable:
                    fields.append(("uint32_t", f"{field_name}_count", False, False, 0, "", "/* Auto-generated array counter */"))
                    fields.append((cpp_type, f"{field_name}", True, True, int(size if size else 1), f"{field_name}_count", ""))
                else:
                    fields.append((cpp_type, f"{field_name}", True, False, int(size if size else 1), "", ""))
            else:
                if ros_full_type in TYPE_MAPPING:
                    cpp_type = TYPE_MAPPING[ros_full_type]
                else:
                    base_type = ros_full_type.split('/')[-1].strip()
                    cpp_type = TYPE_MAPPING.get(base_type, base_type)
                    
                fields.append((cpp_type, field_name, False, False, 0, "", ""))
                
    return fields, constants

def generate_hpp(msg_name, fields, constants):
    includes = set()
    known_primitives = set(TYPE_MAPPING.values()) | {
        "uint8_t", "uint16_t", "uint32_t", "int32_t", "float", "double", "bool", "RosTimestamp"
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
    initializer_list_parts = []

    counter_to_max_size = {}
    for _, f_name, is_array, is_variable, max_size, counter_name, _ in fields:
        if is_array and is_variable:
            counter_to_max_size[counter_name] = (f"MAX_{f_name.upper()}_SIZE", max_size)

    for f_type, f_name, is_array, is_variable, max_size, counter_name, _ in fields:
        if f_type in TYPE_SIZES:
            element_size = TYPE_SIZES[f_type]
        else:
            element_size = f"sizeof({f_type})"

        if is_array:
            initializer_list_parts.append(f"{f_name}{{}}")
        else:
            if f_type == "bool":
                initializer_list_parts.append(f"{f_name}(false)")
            elif f_type == "RosTimestamp":
                initializer_list_parts.append(f"{f_name}{{0, 0}}")
            else:
                initializer_list_parts.append(f"{f_name}(0)")

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

        if is_array:
            if is_variable:
                if f_type in TYPE_SIZES:
                    sequential_deserialize_parts.append(f"        if (offset + {counter_name} * {element_size} > size) return false;\n        std::memcpy({f_name}, src + offset, {counter_name} * {element_size});\n        offset += {counter_name} * {element_size};")
                else:
                    sequential_deserialize_parts.append(f"        if (offset + {counter_name} * sizeof({f_type}) > size) return false;\n        for(uint32_t i = 0; i < {counter_name}; ++i) {{\n            std::memcpy(&{f_name}[i], src + offset, sizeof({f_type}));\n            offset += sizeof({f_type});\n        }}")
            else:
                sequential_deserialize_parts.append(f"        if (offset + {max_size} * {element_size} > size) return false;\n        std::memcpy({f_name}, src + offset, {max_size} * {element_size});\n        offset += {max_size} * {element_size};")
        else:
            sequential_deserialize_parts.append(f"        if (offset + sizeof({f_type}) > size) return false;\n        std::memcpy(&{f_name}, src + offset, sizeof({f_type}));\n        offset += sizeof({f_type});")
            
            if f_name in counter_to_max_size:
                const_macro_name, _ = counter_to_max_size[f_name]
                sequential_deserialize_parts.append(f"        if ({f_name} > {const_macro_name}) return false;")

    for _, (const_macro_name, max_size) in counter_to_max_size.items():
        array_max_size_constants.append((const_macro_name, max_size))

    size_expression = " + ".join(size_expr_parts) if size_expr_parts else "0"
    serialize_body = "\n".join(serialize_parts)
    deserialize_body = "\n".join(sequential_deserialize_parts)
    initializer_str = f" : {', '.join(initializer_list_parts)}" if initializer_list_parts else ""

    if has_variable_array:
        fast_path_conditions = []
        for _, f_name, _, is_variable, _, counter_name, _ in fields:
            if is_variable:
                fast_path_conditions.append(f"{counter_name} == MAX_{f_name.upper()}_SIZE")

        fast_path_cond_str = " && ".join(fast_path_conditions)

        smart_size_body = f"""        if ({fast_path_cond_str}) {{
            return sizeof({msg_name});
        }}
        return {size_expression};"""

        smart_serialize_body = f"""        if ({fast_path_cond_str}) {{
            std::memcpy(dest, this, sizeof({msg_name}));
            return sizeof({msg_name});
        }}

        size_t offset = 0;
{serialize_body}
        return offset;"""

        smart_deserialize_body = f"""        if (size == sizeof({msg_name})) {{
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
#include <type_traits>

#pragma pack(push, 1)
class {msg_name} {{
public:
"""
    if constants or array_max_size_constants:
        content += "    // Constants\n"
        for _, c_name, c_val in constants:
            content += f"    static constexpr uint32_t {c_name} = {c_val};\n"
        for const_macro_name, max_size in array_max_size_constants:
            content += f"    static constexpr uint32_t {const_macro_name} = {max_size}; // Auto-generated max array bounds\n"
        content += "\n"

    content += "    // Message Fields\n"
    for f_type, f_name, is_array, _, max_size, _, comment in fields:
        comment_str = f" {comment}" if comment else ""
        if is_array:
            content += f"    {f_type} {f_name}[{max_size}];{comment_str}\n"
        else:
            content += f"    {f_type} {f_name};{comment_str}\n"

    content += f"""
    {msg_name}(){initializer_str} {{
        static_assert(std::is_trivially_copyable<{msg_name}>::value, 
                      "Error: {msg_name} contains non-trivially copyable types! memcpy is unsafe.");
    }}

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
        
    # 1. Scanne zuerst alle verfügbaren .msg-Dateien, um die Namen für das Enum zu kennen
    if not os.path.exists(MSG_DIR):
        print(f"Error: MSG_DIR '{MSG_DIR}' does not exist.")
        return
        
    msg_files = [f for f in os.listdir(MSG_DIR) if f.endswith(".msg")]
    msg_names = [filename[:-4] for filename in msg_files]
    
    # 2. Erstelle die gemeinsame ProtocolCommon.hpp mit dem dynamischen Enum
    create_common_header(msg_names)
    
    # 3. Generiere die einzelnen C++ Klassen-Header
    for filename in msg_files:
        msg_name = filename[:-4]
        fields, constants = parse_msg_file(os.path.join(MSG_DIR, filename))
        generate_hpp(msg_name, fields, constants)
        
    print(f"Generated common header and {len(msg_files)} message classes in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()