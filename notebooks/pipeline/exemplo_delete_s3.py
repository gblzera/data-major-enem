# Databricks notebook source
# esse notebook tem objetivo de mostrar como excluir dados do s3 caso necessário, usar com muito cuidado pois a exclusao é definitiva e nao tem reversao


# antes de excluir sempre:
# 1. liste todos os arquivos para confirmar o que sera excluido
# 2. confira o path duas vezes
# 3. na duvida, pergunte ao grupo ou ao tech lead

# COMMAND ----------

import boto3
import os

# Credenciais
AWS_ACCESS_KEY = dbutils.secrets.get(scope="aws-credentials", key="access-key")
AWS_SECRET_KEY = dbutils.secrets.get(scope="aws-credentials", key="secret-key")

# Config
REGION = "sa-east-1"
BUCKET = "enem-data-lake-gblzera"

# Cliente S3
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)

print("Conectado ao S3")
print(f"   Bucket: {BUCKET}")

class S3Manager:
    def __init__(self, s3_client, bucket):
        self.s3 = s3_client
        self.bucket = bucket
        self.current_path = ""
    
    def clear_screen(self):
        """Limpa a tela com linhas em branco."""
        print("\n" * 2)
    
    def print_header(self, title):
        """Imprime cabeçalho formatado."""
        print("=" * 60)
        print(f"  {title}")
        print("=" * 60)
    
    def print_path(self):
        """Mostra o path atual."""
        path = self.current_path if self.current_path else "(raiz)"
        print(f"\n📍 Local atual: s3://{self.bucket}/{path}")
        print("-" * 60)
    
    def list_contents(self):
        """Lista pastas e arquivos no path atual."""
        response = self.s3.list_objects_v2(
            Bucket=self.bucket,
            Prefix=self.current_path,
            Delimiter="/"
        )
        
        items = []
        
        # Pastas
        for prefix in response.get("CommonPrefixes", []):
            folder_name = prefix["Prefix"][len(self.current_path):]
            items.append({
                "type": "folder",
                "name": folder_name,
                "key": prefix["Prefix"],
                "size": None
            })
        
        # Arquivos
        for obj in response.get("Contents", []):
            # Ignorar o próprio prefixo
            if obj["Key"] == self.current_path:
                continue
            
            file_name = obj["Key"][len(self.current_path):]
            # Ignorar se tiver / (está em subpasta)
            if "/" in file_name:
                continue
                
            items.append({
                "type": "file",
                "name": file_name,
                "key": obj["Key"],
                "size": obj["Size"]
            })
        
        return items
    
    def format_size(self, size_bytes):
        """Formata tamanho em bytes para MB/GB."""
        if size_bytes is None:
            return ""
        
        size_mb = size_bytes / (1024 * 1024)
        if size_mb >= 1024:
            return f"{size_mb / 1024:.2f} GB"
        return f"{size_mb:.2f} MB"
    
    def show_contents(self):
        """Mostra conteúdo do diretório atual."""
        items = self.list_contents()
        
        if not items:
            print("\n  (pasta vazia)")
            return items
        
        print()
        for i, item in enumerate(items):
            if item["type"] == "folder":
                print(f"  [{i}] 📁 {item['name']}")
            else:
                size = self.format_size(item["size"])
                print(f"  [{i}] 📄 {item['name']:<40} {size:>10}")
        
        return items
    
    def go_back(self):
        """Volta um nível no path."""
        if not self.current_path:
            print("\n⚠️  Já está na raiz!")
            return
        
        # Remove última pasta do path
        parts = self.current_path.rstrip("/").split("/")
        if len(parts) > 1:
            self.current_path = "/".join(parts[:-1]) + "/"
        else:
            self.current_path = ""
    
    def enter_folder(self, folder_key):
        """Entra em uma pasta."""
        self.current_path = folder_key
    
    def delete_file(self, key):
        """Exclui um arquivo."""
        self.s3.delete_object(Bucket=self.bucket, Key=key)
    
    def delete_folder(self, prefix):
        """Exclui uma pasta e todo seu conteúdo."""
        response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        
        if "Contents" not in response:
            return 0
        
        count = 0
        for obj in response["Contents"]:
            self.s3.delete_object(Bucket=self.bucket, Key=obj["Key"])
            count += 1
        
        return count
    
    def get_folder_info(self, prefix):
        """Retorna informações de uma pasta."""
        response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        
        if "Contents" not in response:
            return 0, 0
        
        total_size = sum(obj["Size"] for obj in response["Contents"])
        total_files = len(response["Contents"])
        
        return total_files, total_size
    
    def move_file(self, source, dest):
        """Move um arquivo."""
        self.s3.copy_object(
            Bucket=self.bucket,
            CopySource={"Bucket": self.bucket, "Key": source},
            Key=dest
        )
        self.s3.delete_object(Bucket=self.bucket, Key=source)
    
    def menu_principal(self):
        """Menu principal de navegação."""
        while True:
            self.clear_screen()
            self.print_header("GERENCIADOR S3 - DATA MAJOR")
            self.print_path()
            
            items = self.show_contents()
            
            print("\n" + "-" * 60)
            print("  AÇÕES:")
            print("  [numero] Acessar pasta/arquivo")
            print("  [v]      Voltar pasta anterior")
            print("  [d]      Deletar arquivos/pasta")
            print("  [m]      Mover arquivo")
            print("  [r]      Recarregar")
            print("  [q]      Sair")
            print("-" * 60)
            
            opcao = input("\n👉 Opção: ").strip().lower()
            
            if opcao == "q":
                print("\n👋 Até mais!")
                break
            
            elif opcao == "v":
                self.go_back()
            
            elif opcao == "r":
                continue
            
            elif opcao == "d":
                self.menu_deletar(items)
            
            elif opcao == "m":
                self.menu_mover(items)
            
            elif opcao.isdigit():
                idx = int(opcao)
                if 0 <= idx < len(items):
                    item = items[idx]
                    if item["type"] == "folder":
                        self.enter_folder(item["key"])
                    else:
                        self.menu_arquivo(item)
                else:
                    print("\n❌ Índice inválido!")
                    input("Pressione Enter para continuar...")
            
            else:
                print("\n❌ Opção inválida!")
                input("Pressione Enter para continuar...")
    
    def menu_deletar(self, items):
        """Menu de exclusão."""
        if not items:
            print("\n⚠️  Nenhum item para deletar!")
            input("Pressione Enter para continuar...")
            return
        
        self.clear_screen()
        self.print_header("🗑️  DELETAR ARQUIVOS/PASTAS")
        self.print_path()
        
        print()
        for i, item in enumerate(items):
            tipo = "📁" if item["type"] == "folder" else "📄"
            size = self.format_size(item["size"]) if item["size"] else ""
            print(f"  [{i}] {tipo} {item['name']:<40} {size}")
        
        print("\n" + "-" * 60)
        print("  OPÇÕES:")
        print("  [numeros]  Deletar específicos (ex: 0,2,3)")
        print("  [todos]    Deletar TODOS os itens")
        print("  [pasta]    Deletar pasta atual e TUDO dentro")
        print("  [c]        Cancelar")
        print("-" * 60)
        
        opcao = input("\n👉 O que deletar: ").strip().lower()
        
        if opcao == "c":
            return
        
        elif opcao == "todos":
            # Confirmar exclusão de todos
            total_files = len([i for i in items if i["type"] == "file"])
            total_folders = len([i for i in items if i["type"] == "folder"])
            
            print(f"\n⚠️  Você vai deletar:")
            print(f"   • {total_files} arquivo(s)")
            print(f"   • {total_folders} pasta(s) (e todo conteúdo)")
            
            confirm = input("\n🔴 Confirmar exclusão? (digite 'sim'): ").strip().lower()
            
            if confirm != "sim":
                print("\n❌ Operação cancelada.")
                input("Pressione Enter para continuar...")
                return
            
            print("\n🗑️  Deletando...")
            for item in items:
                if item["type"] == "folder":
                    count = self.delete_folder(item["key"])
                    print(f"   ✅ Pasta {item['name']} ({count} arquivos)")
                else:
                    self.delete_file(item["key"])
                    print(f"   ✅ {item['name']}")
            
            print("\n✅ Tudo deletado!")
            input("Pressione Enter para continuar...")
        
        elif opcao == "pasta":
            if not self.current_path:
                print("\n❌ Não pode deletar a raiz do bucket!")
                input("Pressione Enter para continuar...")
                return
            
            files, size = self.get_folder_info(self.current_path)
            size_str = self.format_size(size)
            
            print(f"\n⚠️  Você vai deletar a pasta INTEIRA:")
            print(f"   📁 {self.current_path}")
            print(f"   • {files} arquivo(s)")
            print(f"   • {size_str}")
            
            confirm = input("\n🔴 Confirmar exclusão? (digite 'sim'): ").strip().lower()
            
            if confirm != "sim":
                print("\n❌ Operação cancelada.")
                input("Pressione Enter para continuar...")
                return
            
            print("\n🗑️  Deletando pasta...")
            count = self.delete_folder(self.current_path)
            print(f"   ✅ {count} arquivos deletados")
            
            # Voltar um nível
            self.go_back()
            
            print("\n✅ Pasta deletada!")
            input("Pressione Enter para continuar...")
        
        else:
            # Deletar índices específicos
            try:
                indices = [int(x.strip()) for x in opcao.split(",")]
            except:
                print("\n❌ Formato inválido! Use: 0,2,3")
                input("Pressione Enter para continuar...")
                return
            
            # Validar índices
            itens_deletar = []
            for idx in indices:
                if 0 <= idx < len(items):
                    itens_deletar.append(items[idx])
                else:
                    print(f"\n❌ Índice {idx} inválido!")
                    input("Pressione Enter para continuar...")
                    return
            
            print(f"\n⚠️  Você vai deletar {len(itens_deletar)} item(s):")
            for item in itens_deletar:
                tipo = "📁" if item["type"] == "folder" else "📄"
                print(f"   {tipo} {item['name']}")
            
            confirm = input("\n🔴 Confirmar exclusão? (digite 'sim'): ").strip().lower()
            
            if confirm != "sim":
                print("\n❌ Operação cancelada.")
                input("Pressione Enter para continuar...")
                return
            
            print("\n🗑️  Deletando...")
            for item in itens_deletar:
                if item["type"] == "folder":
                    count = self.delete_folder(item["key"])
                    print(f"   ✅ Pasta {item['name']} ({count} arquivos)")
                else:
                    self.delete_file(item["key"])
                    print(f"   ✅ {item['name']}")
            
            print("\n✅ Deletado!")
            input("Pressione Enter para continuar...")
    
    def menu_arquivo(self, item):
        """Menu de ações para um arquivo."""
        while True:
            self.clear_screen()
            self.print_header(f"📄 {item['name']}")
            
            print(f"\n  Path: {item['key']}")
            print(f"  Tamanho: {self.format_size(item['size'])}")
            
            print("\n" + "-" * 60)
            print("  AÇÕES:")
            print("  [d]  Deletar arquivo")
            print("  [m]  Mover arquivo")
            print("  [v]  Voltar")
            print("-" * 60)
            
            opcao = input("\n👉 Opção: ").strip().lower()
            
            if opcao == "v":
                break
            
            elif opcao == "d":
                print(f"\n⚠️  Deletar: {item['name']}")
                confirm = input("🔴 Confirmar? (digite 'sim'): ").strip().lower()
                
                if confirm == "sim":
                    self.delete_file(item["key"])
                    print("\n✅ Arquivo deletado!")
                    input("Pressione Enter para continuar...")
                    break
                else:
                    print("\n❌ Cancelado.")
                    input("Pressione Enter para continuar...")
            
            elif opcao == "m":
                print(f"\n📦 Mover: {item['name']}")
                print(f"   De: {item['key']}")
                
                novo_path = input("\n   Para (path completo): ").strip()
                
                if not novo_path:
                    print("\n❌ Path vazio!")
                    input("Pressione Enter para continuar...")
                    continue
                
                print(f"\n⚠️  Mover:")
                print(f"   De:   {item['key']}")
                print(f"   Para: {novo_path}")
                
                confirm = input("\n🔴 Confirmar? (digite 'sim'): ").strip().lower()
                
                if confirm == "sim":
                    self.move_file(item["key"], novo_path)
                    print("\n✅ Arquivo movido!")
                    input("Pressione Enter para continuar...")
                    break
                else:
                    print("\n❌ Cancelado.")
                    input("Pressione Enter para continuar...")
    
    def menu_mover(self, items):
        """Menu para mover arquivos."""
        arquivos = [i for i in items if i["type"] == "file"]
        
        if not arquivos:
            print("\n⚠️  Nenhum arquivo para mover!")
            input("Pressione Enter para continuar...")
            return
        
        self.clear_screen()
        self.print_header("📦 MOVER ARQUIVOS")
        self.print_path()
        
        print("\n  Arquivos disponíveis:")
        for i, item in enumerate(arquivos):
            size = self.format_size(item["size"])
            print(f"  [{i}] 📄 {item['name']:<40} {size}")
        
        print("\n" + "-" * 60)
        
        opcao = input("\n👉 Qual arquivo mover (número ou 'c' para cancelar): ").strip().lower()
        
        if opcao == "c":
            return
        
        try:
            idx = int(opcao)
            if idx < 0 or idx >= len(arquivos):
                raise ValueError()
        except:
            print("\n❌ Índice inválido!")
            input("Pressione Enter para continuar...")
            return
        
        item = arquivos[idx]
        print(f"\n📦 Mover: {item['name']}")
        print(f"   Atual: {item['key']}")
        
        novo_path = input("\n   Novo path completo: ").strip()
        
        if not novo_path:
            print("\n❌ Path vazio!")
            input("Pressione Enter para continuar...")
            return
        
        print(f"\n⚠️  Confirmar:")
        print(f"   De:   {item['key']}")
        print(f"   Para: {novo_path}")
        
        confirm = input("\n🔴 Mover? (digite 'sim'): ").strip().lower()
        
        if confirm == "sim":
            self.move_file(item["key"], novo_path)
            print("\n✅ Movido!")
        else:
            print("\n❌ Cancelado.")
        
        input("Pressione Enter para continuar...")


print("\n🚀 Iniciando Gerenciador Interativo S3...")
print("   Use os menus para navegar e gerenciar arquivos.\n")

manager = S3Manager(s3, BUCKET)
manager.menu_principal()
