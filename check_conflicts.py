import os
import ast
from collections import defaultdict

def find_model_definitions(directory):
    all_models = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Parse the AST
                    tree = ast.parse(content)
                    
                    # Find class definitions that inherit from models.Model
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            # Check if it inherits from models.Model or BaseTestModel
                            for base in node.bases:
                                if isinstance(base, ast.Attribute):
                                    if (base.attr == 'Model' and 
                                        isinstance(base.value, ast.Name) and 
                                        base.value.id == 'models'):
                                        all_models.append((node.name, file_path))
                                elif isinstance(base, ast.Name):
                                    if base.id in ['BaseTestModel', 'Model']:
                                        all_models.append((node.name, file_path))
                
                except Exception as e:
                    print(f'Error parsing {file_path}: {e}')
    
    return all_models

# Find all model definitions
all_models = find_model_definitions('tests')

# Group by model name (case-insensitive)
model_groups = defaultdict(list)
for model_name, file_path in all_models:
    model_groups[model_name.lower()].append((model_name, file_path))

# Find conflicts
print('Model name conflicts:')
conflicts_found = False
for normalized_name, models in model_groups.items():
    if len(models) > 1:
        conflicts_found = True
        print(f'\nConflict for "{normalized_name}":')
        for model_name, file_path in models:
            print(f'  - {model_name} in {file_path}')

if not conflicts_found:
    print('No direct model name conflicts found.')
    
# Check for similar names that might cause table name conflicts
print('\nChecking for potential table name conflicts...')
table_names = {}
for model_name, file_path in all_models:
    # Django generates table names as app_label + '_' + model_name.lower()
    table_name = f'tests_{model_name.lower()}'
    if table_name in table_names:
        print(f'TABLE CONFLICT: {table_name}')
        print(f'  - {table_names[table_name][0]} in {table_names[table_name][1]}')
        print(f'  - {model_name} in {file_path}')
    else:
        table_names[table_name] = (model_name, file_path)

print(f'\nTotal models found: {len(all_models)}')
print(f'Unique table names: {len(table_names)}')