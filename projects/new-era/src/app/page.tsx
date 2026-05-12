const skills = [
  "TypeScript", "React", "Next.js", "Node.js",
  "PostgreSQL", "Docker", "Tailwind CSS", "Git",
];

const projects = [
  {
    title: "Home Server Setup",
    description: "Self-hosted infrastructure with Docker, reverse proxy, and automated backups running on a local machine.",
    tags: ["Docker", "Linux", "Nginx"],
    href: "#",
  },
  {
    title: "Keep It Real",
    description: "A monorepo of personal projects and experiments — from web apps to automation scripts.",
    tags: ["Monorepo", "Next.js", "TypeScript"],
    href: "#",
  },
  {
    title: "CLI Tooling",
    description: "Custom command-line utilities to automate repetitive dev tasks and boost daily productivity.",
    tags: ["Node.js", "Shell", "Bash"],
    href: "#",
  },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 font-sans">
      {/* Nav */}
      <nav className="sticky top-0 z-10 border-b border-zinc-100 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/80 backdrop-blur">
        <div className="max-w-3xl mx-auto px-6 h-14 flex items-center justify-between">
          <span className="font-semibold tracking-tight">Richard Nguyen</span>
          <div className="flex gap-6 text-sm text-zinc-500 dark:text-zinc-400">
            <a href="#about" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">About</a>
            <a href="#skills" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">Skills</a>
            <a href="#projects" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">Projects</a>
            <a href="#contact" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">Contact</a>
          </div>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto px-6 py-20 space-y-24">
        {/* Hero */}
        <section id="about" className="space-y-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-indigo-400 to-violet-600 flex items-center justify-center text-white text-2xl font-bold select-none">
              R
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Richard Nguyen</h1>
              <p className="text-zinc-500 dark:text-zinc-400 text-sm">Full-Stack Developer · Ho Chi Minh City, Vietnam</p>
            </div>
          </div>
          <p className="text-lg leading-8 text-zinc-600 dark:text-zinc-400 max-w-xl">
            I build things for the web — from snappy frontends to reliable backend services.
            Passionate about clean code, self-hosting, and turning ideas into real products.
          </p>
          <div className="flex gap-3">
            <a
              href="https://github.com/richardnguyen0715"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-full bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 px-5 py-2 text-sm font-medium hover:opacity-80 transition-opacity"
            >
              GitHub
            </a>
            <a
              href="mailto:hello@richardnguyen.dev"
              className="inline-flex items-center gap-2 rounded-full border border-zinc-200 dark:border-zinc-700 px-5 py-2 text-sm font-medium hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
            >
              Email me
            </a>
          </div>
        </section>

        {/* Skills */}
        <section id="skills" className="space-y-5">
          <h2 className="text-xl font-semibold tracking-tight">Skills</h2>
          <div className="flex flex-wrap gap-2">
            {skills.map((skill) => (
              <span
                key={skill}
                className="px-3 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 text-sm font-medium"
              >
                {skill}
              </span>
            ))}
          </div>
        </section>

        {/* Projects */}
        <section id="projects" className="space-y-5">
          <h2 className="text-xl font-semibold tracking-tight">Projects</h2>
          <div className="grid gap-4">
            {projects.map((project) => (
              <a
                key={project.title}
                href={project.href}
                className="group block rounded-xl border border-zinc-100 dark:border-zinc-800 p-5 hover:border-zinc-300 dark:hover:border-zinc-600 hover:shadow-sm transition-all"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <h3 className="font-semibold group-hover:text-indigo-500 transition-colors">
                      {project.title}
                    </h3>
                    <p className="text-sm text-zinc-500 dark:text-zinc-400 leading-6">
                      {project.description}
                    </p>
                  </div>
                  <span className="text-zinc-300 dark:text-zinc-600 group-hover:text-indigo-400 transition-colors shrink-0 mt-1">→</span>
                </div>
                <div className="flex flex-wrap gap-2 mt-3">
                  {project.tags.map((tag) => (
                    <span key={tag} className="text-xs px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400">
                      {tag}
                    </span>
                  ))}
                </div>
              </a>
            ))}
          </div>
        </section>

        {/* Contact */}
        <section id="contact" className="space-y-4 pb-10">
          <h2 className="text-xl font-semibold tracking-tight">Get in touch</h2>
          <p className="text-zinc-500 dark:text-zinc-400 leading-7">
            Have a project in mind or just want to chat? Feel free to reach out — I&apos;m always open to interesting conversations.
          </p>
          <a
            href="mailto:hello@richardnguyen.dev"
            className="inline-flex items-center gap-2 text-indigo-500 hover:text-indigo-600 font-medium transition-colors"
          >
            hello@richardnguyen.dev →
          </a>
        </section>
      </main>

      <footer className="border-t border-zinc-100 dark:border-zinc-800 text-center py-6 text-xs text-zinc-400 dark:text-zinc-600">
        © {new Date().getFullYear()} Richard Nguyen. Built with Next.js &amp; Tailwind CSS.
      </footer>
    </div>
  );
}
