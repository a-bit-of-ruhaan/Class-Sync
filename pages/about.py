import base64
from textwrap import dedent

import streamlit as st

from backend.auth import require_auth

st.set_page_config(
	page_title="About ClassSync",
	layout="wide",
)

require_auth()

with open("styles/about.css") as f:
	page_css = f.read()
with open("images/backg.png", "rb") as f:
	background_image = base64.b64encode(f.read()).decode("ascii")
st.markdown(
	f"<style>{page_css.replace('images/backg.png', f'data:image/png;base64,{background_image}')}</style>",
	unsafe_allow_html=True,
)

st.html(
	dedent(
	"""
	<div class="about_page_header">
	<main class="about_page">
		<header class="team_header">
			<span class="team_kicker">MEET THE PEOPLE BEHIND CLASSYNC</span>
			<h1>TEAM</h1>
			<p>Three curious minds building a calmer way to learn, organize, and grow.</p>
		</header>
    </div>
		<section class="team_list" aria-label="Classync development team">
		    <article class="team_member team_leader">
							<div class="member_info">
								<span class="member_role">TEAM LEADER</span>
								<h2>Ruhaan</h2>
								<a class="portfolio_button" href="https://a-bit-of-ruhaan.github.io/My-Portfolio/" target="_blank" rel="noopener noreferrer">View portfolio <span aria-hidden="true">↗</span></a>
								<p>Ruhaan leads Classync with a focus on useful learning tools and a warm, human experience. He keeps the team moving from concept to working product.</p>
								<span class="member_tag">VISION &amp; DIRECTION</span>
							</div>
							<div class="member_visual" aria-label="Ruhaan image holder">
								<div class="member_avatar">R</div>
								<span class="avatar_caption">RUHAAN</span>
							</div>
						</article>

			<article class="team_member">
				<div class="member_info">
					<span class="member_role">MEMBER 01</span>
					<h2>Ashish</h2>
					<a class="portfolio_button" href="#" target="_blank" rel="noopener noreferrer">View portfolio <span aria-hidden="true">↗</span></a>
					<p>Ashish brings a practical eye for clean experiences and thoughtful details. He enjoys turning useful ideas into features that feel simple to use.</p>
					<span class="member_tag">PRODUCT THINKER</span>
				</div>
				<div class="member_visual" aria-label="Ashish image holder">
					<div class="member_avatar">A</div>
					<span class="avatar_caption">ASHISH</span>
				</div>
			</article>

			<article class="team_member">
				<div class="member_info">
					<span class="member_role">MEMBER 02</span>
					<h2>Vansh</h2>
					<a class="portfolio_button" href="#" target="_blank" rel="noopener noreferrer">View portfolio <span aria-hidden="true">↗</span></a>
					<p>Vansh brings energy, experimentation, and a sharp curiosity to the team. He likes exploring new approaches until the right solution clicks.</p>
					<span class="member_tag">IDEA EXPLORER</span>
				</div>
				<div class="member_visual" aria-label="Vansh image holder">
					<div class="member_avatar">V</div>
					<span class="avatar_caption">VANSH</span>
				</div>
			</article>
		</section>
	</main>
	""",
	),
)
