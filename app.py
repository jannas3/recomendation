import streamlit as st

import pandas as pd
from math import sqrt
from sklearn.metrics.pairwise import cosine_similarity
# CSS personalizado
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://img.freepik.com/fotos-gratis/colagem-de-fundo-de-filme_23-2149876030.jpg");
        background-size: cover;
        background-position: center;
        color: #000000;
    }
   h1 {
        color: #FFD700;  /* Laranja Claro */
    }
    h2 {
        color: #00FFFF;  /* Ciano */
    }
    h3 {
        color: #FFFFE0;  /* Amarelo Claro */
    }
    p{
     color: #FFFFFF;
    }
    h4, h5, h6, div {
        color: #000000;  /* Branco */
    }
    div.stButton > button:first-child {
        background-color: #000080;
        color: #FFFFFF;
        border: None;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: bold;
    }
    div.stButton > button:first-child:hover {
        background-color: #0000A0;
        color: #FFFFFF;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Caminho relativo dos arquivos (servidor)
filmes_path = 'dados/movies.csv'
rating_path = 'dados/ratings.csv'

# Leitura dos dados
filmes = pd.read_csv(filmes_path)
ratings = pd.read_csv(rating_path)
# Amostragem de 50 filmes
amostra_filmes = filmes.sample(n=50, random_state=1)
filmes = amostra_filmes

# Inicializando dados persistentes no Streamlit
def init_session_state():
    if 'avaliacoesUsers' not in st.session_state:
        st.session_state.avaliacoesUsers = {}
    if 'avaliacoesModel' not in st.session_state:
        st.session_state.avaliacoesModel = {
            'Model': set(filmes['title'].unique())
        }
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'menu' not in st.session_state:
        st.session_state.menu = 'main'

init_session_state()

# Construindo a matriz de avaliação
rating_matrix = ratings.pivot(index='movieId', columns='userId', values='rating').fillna(0)

# Calculando a similaridade entre itens usando cosseno
item_similarity = cosine_similarity(rating_matrix)
item_similarity_df = pd.DataFrame(item_similarity, index=rating_matrix.index, columns=rating_matrix.index)

# Função de recomendação baseada em itens
def get_item_based_recommendations(user_id, rating_matrix, item_similarity_df, filmes_df, n=10):
    user_ratings = rating_matrix[user_id]
    weighted_sum = item_similarity_df.dot(user_ratings)
    similarity_sum = item_similarity_df.sum(axis=1)
    
    similarity_sum[similarity_sum == 0] = 1  # Evita divisão por zero
    predicted_ratings = weighted_sum / similarity_sum
    predicted_ratings = predicted_ratings[user_ratings == 0]
    
    # Filtra apenas os filmes na amostra
    recommended_movie_ids = predicted_ratings.index.intersection(filmes_df['movieId'])
    recommendations = predicted_ratings.loc[recommended_movie_ids].sort_values(ascending=False).head(n)
    
    recommended_titles = []
    for movie_id in recommendations.index:
        movie_title = filmes_df[filmes_df['movieId'] == movie_id]['title'].values
        if len(movie_title) > 0:
            recommended_titles.append(movie_title[0])
        else:
            st.write(f"Filme ID {movie_id} não encontrado na base de filmes.")
    
    if not recommended_titles:
        st.write("Nenhum filme recomendado encontrado na base de dados de filmes.")
    
    return recommended_titles

# Funções de gerenciamento de usuários
def new_user(user):
    if user in st.session_state.avaliacoesUsers:
        return False
    st.session_state.avaliacoesUsers[user] = {}
    return True

def user_exists(user):
    return user in st.session_state.avaliacoesUsers

def add_movie(movie_title, user, nota):
    if movie_title in st.session_state.avaliacoesModel['Model']:
        if movie_title not in st.session_state.avaliacoesUsers[user]:
            st.session_state.avaliacoesUsers[user][movie_title] = nota
            return True
    return False

def get_user_movies(user):
    return list(st.session_state.avaliacoesUsers[user].items())

def delete_movie(user, movie_title):
    if movie_title in st.session_state.avaliacoesModel['Model'] and movie_title in st.session_state.avaliacoesUsers[user]:
        del st.session_state.avaliacoesUsers[user][movie_title]
        return True
    return False

def update_rating(user, movie_title, nota):
    if movie_title in st.session_state.avaliacoesUsers[user]:
        st.session_state.avaliacoesUsers[user][movie_title] = nota
        return True
    return False

def delete_profile(user):
    if user in st.session_state.avaliacoesUsers:
        del st.session_state.avaliacoesUsers[user]
        return True
    return False

# Funções para Streamlit
def main_menu():
    st.title("🎬 Sistema de Recomendação")
    choice = st.selectbox("Escolha uma opção:", ["Acessar Perfil", "Criar Novo Perfil", "Sair"])
    return choice

def perfil_menu():
    st.title("Menu de Usuário")
    choice = st.selectbox("Escolha uma opção:", ["Histórico de Filmes", "Adicionar Filme", "Excluir Filme", "Filmes Recomendados", "Mudar Nota", "Excluir Perfil", "Voltar ao Menu Principal"])
    return choice

def criar_perfil():
    st.title("Novo Usuário")
    name = st.text_input("Digite seu nome de usuário:")
    if st.button("Criar"):
        if new_user(name):
            st.success(f"Usuário {name} criado com sucesso!")
        else:
            st.error("Nome já existente, crie um novo.")

def acessar_perfil():
    nome = st.session_state.current_user
    st.write(f"Bem-vindo, {nome}!")
    choice = perfil_menu()
    
    if choice == "Histórico de Filmes":
        historico = get_user_movies(nome)
        if historico:
            st.write("Histórico de Filmes:")
            for item in historico:
                st.write(f"{item[0]}: {item[1]}")
        else:
            st.write("Não há filmes adicionados.")
    
    elif choice == "Adicionar Filme":
        filmes_disponiveis = list(st.session_state.avaliacoesModel['Model'] - set(st.session_state.avaliacoesUsers[nome].keys()))
        if filmes_disponiveis:
            movie = st.selectbox("Escolha um filme para adicionar:", filmes_disponiveis)
            nota = st.slider("Qual a nota desse filme? (0.0 - 5.0)", 0.0, 5.0, step=0.5)
            if st.button("Adicionar"):
                if add_movie(movie, nome, nota):
                    st.success(f"Filme {movie} adicionado com nota {nota}!")
                else:
                    st.error("Filme já adicionado ou não encontrado.")
        else:
            st.write("Sem filmes disponíveis para adicionar.")
    
    elif choice == "Excluir Filme":
        movie = st.text_input("Qual filme deseja excluir?")
        if st.button("Excluir"):
            if delete_movie(nome, movie):
                st.success(f"Filme {movie} excluído!")
            else:
                st.error("Filme não encontrado ou não está na lista.")
    
    elif choice == "Filmes Recomendados":
        recomendacoes = get_item_based_recommendations(user_id=1, rating_matrix=rating_matrix, item_similarity_df=item_similarity_df, filmes_df=filmes)
        if recomendacoes:  # Verifica se a lista não está vazia
            st.write("Filmes Recomendados:")
            for movie in recomendacoes:
                st.write(f"{movie}")
        else:
            st.write("Sem filmes para recomendar.")
    
    elif choice == "Mudar Nota":
        movie = st.text_input("Qual filme deseja mudar a nota?")
        nota = st.slider("Nova nota:", 0.0, 5.0, step=0.5)
        if st.button("Mudar Nota"):
            if update_rating(nome, movie, nota):
                st.success(f"Nota do filme {movie} modificada para {nota}!")
            else:
                st.error("Filme não encontrado no histórico.")
    
    elif choice == "Excluir Perfil":
        if st.button("Excluir Perfil"):
            if delete_profile(nome):
                st.success(f"Perfil {nome} excluído!")
                st.session_state.current_user = None
                st.session_state.menu = 'main'
            else:
                st.error("Erro ao excluir perfil.")
    
    elif choice == "Voltar ao Menu Principal":
        st.session_state.menu = 'main'

def main():
    if st.session_state.menu == 'main':
        choice = main_menu()
        if choice == "Acessar Perfil":
            nome = st.text_input("Nome do Usuário:")
            if st.button("Entrar"):
                if user_exists(nome):
                    st.session_state.current_user = nome
                    st.session_state.menu = 'perfil'
                else:
                    st.error("Usuário não encontrado.")
        elif choice == "Criar Novo Perfil":
            criar_perfil()
        elif choice == "Sair":
            st.write("Saindo...")
    
    elif st.session_state.menu == 'perfil':
        acessar_perfil()

if __name__ == "__main__":
    main()
