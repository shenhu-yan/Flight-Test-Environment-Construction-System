import os
import json
import uuid
from datetime import datetime


class ModelManager:
    def __init__(self):
        self.upload_dir = 'uploads/models'
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def generate_model_id(self, project_id, task_id, model_type):
        """生成模型唯一ID"""
        serial_no = str(uuid.uuid4().hex[:4])
        return f"SERI_MDL_{project_id}_{task_id}_{model_type}_{serial_no}"
    
    def upload_model(self, file, project_id, task_id, model_type, version, description):
        """上传模型"""
        # 生成模型ID
        model_id = self.generate_model_id(project_id, task_id, model_type)
        
        # 确保项目目录存在
        project_dir = os.path.join(self.upload_dir, project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        # 保存文件
        file_name = f"{model_id}_{file.filename}"
        file_path = os.path.join(project_dir, file_name)
        file.save(file_path)
        
        return {
            'model_id': model_id,
            'file_path': file_path,
            'file_name': file_name
        }
    
    def download_model(self, model_id, project_id):
        """下载模型"""
        project_dir = os.path.join(self.upload_dir, project_id)
        if not os.path.exists(project_dir):
            return None
        
        # 查找模型文件
        for file_name in os.listdir(project_dir):
            if file_name.startswith(model_id):
                file_path = os.path.join(project_dir, file_name)
                return file_path
        
        return None
    
    def delete_model(self, model_id, project_id):
        """删除模型"""
        project_dir = os.path.join(self.upload_dir, project_id)
        if not os.path.exists(project_dir):
            return False
        
        # 查找并删除模型文件
        for file_name in os.listdir(project_dir):
            if file_name.startswith(model_id):
                file_path = os.path.join(project_dir, file_name)
                os.remove(file_path)
                return True
        
        return False
    
    def get_model_info(self, model_id, project_id):
        """获取模型信息"""
        project_dir = os.path.join(self.upload_dir, project_id)
        if not os.path.exists(project_dir):
            return None
        
        # 查找模型文件
        for file_name in os.listdir(project_dir):
            if file_name.startswith(model_id):
                file_path = os.path.join(project_dir, file_name)
                file_size = os.path.getsize(file_path)
                modified_time = os.path.getmtime(file_path)
                
                return {
                    'model_id': model_id,
                    'file_name': file_name,
                    'file_path': file_path,
                    'file_size': file_size,
                    'modified_time': datetime.fromtimestamp(modified_time).isoformat()
                }
        
        return None
    
    def list_models(self, project_id, model_type=None):
        """列出项目中的模型"""
        project_dir = os.path.join(self.upload_dir, project_id)
        if not os.path.exists(project_dir):
            return []
        
        models = []
        for file_name in os.listdir(project_dir):
            # 解析模型ID
            parts = file_name.split('_')
            if len(parts) >= 6 and parts[0] == 'SERI' and parts[1] == 'MDL':
                model_id = '_'.join(parts[:6])
                file_path = os.path.join(project_dir, file_name)
                file_size = os.path.getsize(file_path)
                modified_time = os.path.getmtime(file_path)
                
                model_info = {
                    'model_id': model_id,
                    'file_name': file_name,
                    'file_path': file_path,
                    'file_size': file_size,
                    'modified_time': datetime.fromtimestamp(modified_time).isoformat()
                }
                
                # 过滤模型类型
                if model_type:
                    if model_id.split('_')[4] == model_type:
                        models.append(model_info)
                else:
                    models.append(model_info)
        
        return models
    
    def backup_project_models(self, project_id):
        """备份项目模型"""
        import shutil
        
        project_dir = os.path.join(self.upload_dir, project_id)
        if not os.path.exists(project_dir):
            return None
        
        backup_dir = os.path.join('backups', f"{project_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(backup_dir, exist_ok=True)
        
        # 复制所有模型文件
        for file_name in os.listdir(project_dir):
            src_path = os.path.join(project_dir, file_name)
            dst_path = os.path.join(backup_dir, file_name)
            shutil.copy2(src_path, dst_path)
        
        return backup_dir
    
    def restore_project_models(self, project_id, backup_path):
        """恢复项目模型"""
        import shutil
        
        project_dir = os.path.join(self.upload_dir, project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        # 复制备份文件到项目目录
        for file_name in os.listdir(backup_path):
            src_path = os.path.join(backup_path, file_name)
            dst_path = os.path.join(project_dir, file_name)
            shutil.copy2(src_path, dst_path)
        
        return True
    
    def validate_model(self, file_path):
        """验证模型文件"""
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return False, 'File not found'
        
        # 检查文件大小（限制为100MB）
        max_size = 100 * 1024 * 1024  # 100MB
        if os.path.getsize(file_path) > max_size:
            return False, 'File too large (max 100MB)'
        
        # 检查文件扩展名
        valid_extensions = ['.pth', '.pt', '.onnx', '.h5', '.pb', '.json', '.xml']
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in valid_extensions:
            return False, 'Invalid file format'
        
        return True, 'Valid model file'
    
    def get_model_versions(self, project_id, task_id, model_type):
        """获取模型版本历史"""
        project_dir = os.path.join(self.upload_dir, project_id)
        if not os.path.exists(project_dir):
            return []
        
        versions = []
        for file_name in os.listdir(project_dir):
            # 解析模型ID
            parts = file_name.split('_')
            if len(parts) >= 6 and parts[0] == 'SERI' and parts[1] == 'MDL':
                model_project_id = parts[2]
                model_task_id = parts[3]
                model_model_type = parts[4]
                
                if model_project_id == project_id and model_task_id == task_id and model_model_type == model_type:
                    model_id = '_'.join(parts[:6])
                    file_path = os.path.join(project_dir, file_name)
                    file_size = os.path.getsize(file_path)
                    modified_time = os.path.getmtime(file_path)
                    
                    # 提取版本号（假设文件名中包含版本信息）
                    version = '1.0.0'  # 默认版本
                    if len(parts) > 6:
                        version = parts[6].split('.')[0]  # 简单提取版本号
                    
                    versions.append({
                        'model_id': model_id,
                        'version': version,
                        'file_name': file_name,
                        'file_size': file_size,
                        'modified_time': datetime.fromtimestamp(modified_time).isoformat()
                    })
        
        # 按修改时间排序，最新的在前
        versions.sort(key=lambda x: x['modified_time'], reverse=True)
        
        return versions
