import React, { useState, useEffect, useRef } from 'react';
import { Terminal, X, Minimize2, Maximize2 } from 'lucide-react';

export default function WebTerminal() {
  const [history, setHistory] = useState([
    { type: 'output', content: 'Web Terminal v2.0.0 - Full Command Support' },
    { type: 'output', content: 'Type "help" for available commands' }
  ]);
  const [input, setInput] = useState('');
  const [commandHistory, setCommandHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [currentPath, setCurrentPath] = useState('~');
  const [fileSystem, setFileSystem] = useState({
    '~': {
      type: 'dir',
      contents: {
        'documents': { type: 'dir', contents: {} },
        '.local': { 
          type: 'dir', 
          contents: {
            'bin': { type: 'dir', contents: {} }
          }
        },
        'readme.txt': { type: 'file', content: 'Welcome to Web Terminal!', permissions: 'rw-r--r--' }
      }
    }
  });
  const [installedPackages, setInstalledPackages] = useState(['base-system']);
  const [isMinimized, setIsMinimized] = useState(false);
  const [environment, setEnvironment] = useState({
    PATH: '~/.local/bin:/usr/local/bin:/usr/bin:/bin',
    USER: 'guest',
    HOME: '~',
    SHELL: '/bin/bash'
  });
  const inputRef = useRef(null);
  const terminalRef = useRef(null);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [history]);

  const resolvePath = (path) => {
    if (!path || path === '~') return '~';
    if (path.startsWith('~')) return path;
    if (path.startsWith('/')) return '~' + path;
    return currentPath === '~' ? `~/${path}` : `${currentPath}/${path}`;
  };

  const getNode = (path) => {
    const parts = path.split('/').filter(p => p && p !== '~');
    let node = fileSystem['~'];
    for (const part of parts) {
      if (!node.contents || !node.contents[part]) return null;
      node = node.contents[part];
    }
    return node;
  };

  const setNode = (path, value) => {
    const newFS = JSON.parse(JSON.stringify(fileSystem));
    const parts = path.split('/').filter(p => p && p !== '~');
    let current = newFS['~'];
    
    for (let i = 0; i < parts.length - 1; i++) {
      if (!current.contents[parts[i]]) {
        current.contents[parts[i]] = { type: 'dir', contents: {} };
      }
      current = current.contents[parts[i]];
    }
    
    const lastName = parts[parts.length - 1];
    if (value === null) {
      delete current.contents[lastName];
    } else {
      current.contents[lastName] = value;
    }
    
    setFileSystem(newFS);
  };

  const addOutput = (lines) => {
    const lineArray = Array.isArray(lines) ? lines : [lines];
    setHistory(prev => [...prev, ...lineArray.map(line => ({ type: 'output', content: line }))]);
  };

  const simulateDownload = (url, outputPath, callback) => {
    const fileName = url.split('/').pop() || 'file';
    const lines = [
      `--${new Date().toISOString()}--  ${url}`,
      `Resolving github.com... 140.82.121.4`,
      `Connecting to github.com|140.82.121.4|:443... connected.`,
      `HTTP request sent, awaiting response... 200 OK`,
      `Length: ${Math.floor(Math.random() * 10000000)} (${(Math.random() * 10).toFixed(1)}M) [application/octet-stream]`,
      `Saving to: '${outputPath}'`,
      ``
    ];
    addOutput(lines);

    let progress = 0;
    const interval = setInterval(() => {
      progress += 15;
      const bar = '='.repeat(Math.floor(progress / 5)) + '>' + ' '.repeat(20 - Math.floor(progress / 5));
      addOutput([`[${bar}] ${progress}%`]);
      
      if (progress >= 100) {
        clearInterval(interval);
        addOutput([``, `'${outputPath}' saved`, ``]);
        callback();
      }
    }, 200);
  };

  const commands = {
    help: () => [
      'Available commands:',
      '  Basic: help, clear, echo, date, whoami, uname, env',
      '  Files: ls, cd, pwd, cat, touch, mkdir, rm, cp, mv, chmod',
      '  Network: wget, curl, ping',
      '  Packages: apt, npm, pip, winget',
      '  System: ps, kill, top, df, du, free',
      '  Text: grep, find, head, tail, wc, nano',
      '  Other: calc, weather, history, alias, export',
      '',
      'Use <command> --help for detailed usage'
    ],
    clear: () => {
      setHistory([]);
      return [];
    },
    echo: (args) => {
      const text = args.join(' ');
      return [text.replace(/\$(\w+)/g, (_, v) => environment[v] || '')];
    },
    date: () => [new Date().toString()],
    pwd: () => [currentPath],
    whoami: () => [environment.USER],
    uname: (args) => {
      if (args.includes('-a')) {
        return ['WebTerminal 2.0.0 Web x86_64 GNU/Linux'];
      }
      return ['WebTerminal'];
    },
    env: () => Object.entries(environment).map(([k, v]) => `${k}=${v}`),
    export: (args) => {
      if (args.length === 0) return commands.env();
      const match = args[0].match(/(\w+)=(.*)/);
      if (match) {
        setEnvironment(prev => ({ ...prev, [match[1]]: match[2] }));
        return [];
      }
      return ['export: invalid syntax'];
    },
    ls: (args) => {
      const showAll = args.includes('-a') || args.includes('-la');
      const longFormat = args.includes('-l') || args.includes('-la');
      const path = args.find(a => !a.startsWith('-')) || currentPath;
      const node = getNode(resolvePath(path));
      
      if (!node) return [`ls: cannot access '${path}': No such file or directory`];
      if (node.type !== 'dir') return [path];
      
      const items = Object.entries(node.contents);
      if (items.length === 0) return [];
      
      if (longFormat) {
        return items.map(([name, n]) => {
          const perms = n.permissions || (n.type === 'dir' ? 'drwxr-xr-x' : '-rw-r--r--');
          const size = n.content?.length || 4096;
          return `${perms} 1 guest guest ${size.toString().padStart(8)} Dec 14 12:00 ${name}`;
        });
      }
      
      return items.map(([name]) => name);
    },
    cd: (args) => {
      if (args.length === 0 || args[0] === '~') {
        setCurrentPath('~');
        return [];
      }
      const newPath = resolvePath(args[0]);
      const node = getNode(newPath);
      if (!node) return [`cd: ${args[0]}: No such file or directory`];
      if (node.type !== 'dir') return [`cd: ${args[0]}: Not a directory`];
      setCurrentPath(newPath);
      return [];
    },
    cat: (args) => {
      if (args.length === 0) return ['cat: missing file operand'];
      const path = resolvePath(args[0]);
      const node = getNode(path);
      if (!node) return [`cat: ${args[0]}: No such file or directory`];
      if (node.type !== 'file') return [`cat: ${args[0]}: Is a directory`];
      return (node.content || '').split('\n');
    },
    mkdir: (args) => {
      if (args.length === 0) return ['mkdir: missing operand'];
      const createParents = args.includes('-p');
      const dirName = args.find(a => !a.startsWith('-'));
      if (!dirName) return ['mkdir: missing operand'];
      
      const path = resolvePath(dirName);
      setNode(path, { type: 'dir', contents: {}, permissions: 'drwxr-xr-x' });
      return [];
    },
    touch: (args) => {
      if (args.length === 0) return ['touch: missing file operand'];
      const path = resolvePath(args[0]);
      const existing = getNode(path);
      if (!existing) {
        setNode(path, { type: 'file', content: '', permissions: 'rw-r--r--' });
      }
      return [];
    },
    rm: (args) => {
      if (args.length === 0) return ['rm: missing operand'];
      const recursive = args.includes('-r') || args.includes('-rf');
      const force = args.includes('-f') || args.includes('-rf');
      const target = args.find(a => !a.startsWith('-'));
      
      if (!target) return ['rm: missing operand'];
      const path = resolvePath(target);
      const node = getNode(path);
      
      if (!node) {
        return force ? [] : [`rm: cannot remove '${target}': No such file or directory`];
      }
      
      if (node.type === 'dir' && !recursive) {
        return [`rm: cannot remove '${target}': Is a directory`];
      }
      
      setNode(path, null);
      return [];
    },
    cp: (args) => {
      if (args.length < 2) return ['cp: missing file operand'];
      const src = resolvePath(args[0]);
      const dst = resolvePath(args[1]);
      const node = getNode(src);
      
      if (!node) return [`cp: cannot stat '${args[0]}': No such file or directory`];
      setNode(dst, JSON.parse(JSON.stringify(node)));
      return [];
    },
    mv: (args) => {
      if (args.length < 2) return ['mv: missing file operand'];
      const src = resolvePath(args[0]);
      const dst = resolvePath(args[1]);
      const node = getNode(src);
      
      if (!node) return [`mv: cannot stat '${args[0]}': No such file or directory`];
      setNode(dst, JSON.parse(JSON.stringify(node)));
      setNode(src, null);
      return [];
    },
    chmod: (args) => {
      if (args.length < 2) return ['chmod: missing operand'];
      const perms = args[0];
      const path = resolvePath(args[1]);
      const node = getNode(path);
      
      if (!node) return [`chmod: cannot access '${args[1]}': No such file or directory`];
      
      const newFS = JSON.parse(JSON.stringify(fileSystem));
      const parts = path.split('/').filter(p => p && p !== '~');
      let current = newFS['~'];
      for (let i = 0; i < parts.length - 1; i++) {
        current = current.contents[parts[i]];
      }
      current.contents[parts[parts.length - 1]].permissions = perms;
      setFileSystem(newFS);
      
      return [];
    },
    wget: (args) => {
      if (args.length === 0) return ['wget: missing URL'];
      
      let url = args[0];
      let outputPath = url.split('/').pop();
      
      const oIndex = args.indexOf('-O');
      if (oIndex !== -1 && args[oIndex + 1]) {
        outputPath = args[oIndex + 1];
      }
      
      return new Promise((resolve) => {
        simulateDownload(url, outputPath, () => {
          const fullPath = resolvePath(outputPath);
          setNode(fullPath, {
            type: 'file',
            content: `Downloaded from ${url}`,
            permissions: 'rw-r--r--'
          });
          resolve();
        });
      });
    },
    curl: (args) => {
      if (args.length === 0) return ['curl: no URL specified'];
      const url = args.find(a => !a.startsWith('-')) || args[0];
      
      return new Promise((resolve) => {
        setTimeout(() => {
          addOutput([
            `HTTP/1.1 200 OK`,
            `Content-Type: text/html`,
            ``,
            `<html><body>Content from ${url}</body></html>`
          ]);
          resolve();
        }, 500);
      });
    },
    ping: (args) => {
      if (args.length === 0) return ['ping: missing host'];
      const host = args[0];
      
      return new Promise((resolve) => {
        addOutput([`PING ${host} (93.184.216.34): 56 data bytes`]);
        let count = 0;
        const interval = setInterval(() => {
          const time = (Math.random() * 50 + 10).toFixed(1);
          addOutput([`64 bytes from ${host}: icmp_seq=${count} ttl=64 time=${time} ms`]);
          count++;
          if (count >= 4) {
            clearInterval(interval);
            addOutput([``, `--- ${host} ping statistics ---`, `4 packets transmitted, 4 received, 0% packet loss`]);
            resolve();
          }
        }, 1000);
      });
    },
    winget: (args) => {
      if (args.length === 0) return ['winget: missing command'];
      if (args[0] === 'install') {
        const idIndex = args.indexOf('--id');
        const pkgName = idIndex !== -1 ? args[idIndex + 1] : args[1];
        
        if (!pkgName) return ['winget: missing package name'];
        
        return new Promise((resolve) => {
          addOutput([
            `Found ${pkgName} [${pkgName}]`,
            `This application is licensed to you by its owner.`,
            `Microsoft is not responsible for, nor does it grant any licenses to, third-party packages.`,
            `Downloading ${pkgName}...`
          ]);
          
          let progress = 0;
          const interval = setInterval(() => {
            progress += 20;
            addOutput([`  ██${'█'.repeat(progress / 5)}${'░'.repeat(20 - progress / 5)}  ${progress}%`]);
            
            if (progress >= 100) {
              clearInterval(interval);
              setInstalledPackages(prev => [...prev, `winget:${pkgName}`]);
              addOutput([
                `Successfully installed ${pkgName}`,
                ``
              ]);
              resolve();
            }
          }, 400);
        });
      }
      return ['winget: unknown command'];
    },
    apt: (args) => {
      if (args.length === 0) return ['Usage: apt [install|remove|list|update] <package>'];
      const subCmd = args[0];
      
      if (subCmd === 'update') {
        return new Promise((resolve) => {
          addOutput([`Hit:1 http://archive.ubuntu.com/ubuntu focal InRelease`, `Reading package lists...`]);
          setTimeout(() => {
            addOutput([`All packages are up to date.`]);
            resolve();
          }, 1000);
        });
      }
      
      if (subCmd === 'list') {
        return [
          'Installed packages:',
          ...installedPackages.filter(p => !p.includes(':')).map(pkg => `  ${pkg}`)
        ];
      } else if (subCmd === 'install' && args.length > 1) {
        const pkg = args[1];
        if (installedPackages.includes(pkg)) {
          return [`${pkg} is already the newest version`];
        }
        
        return new Promise((resolve) => {
          addOutput([
            `Reading package lists...`,
            `Building dependency tree...`,
            `The following NEW packages will be installed:`,
            `  ${pkg}`,
            `0 upgraded, 1 newly installed, 0 to remove`,
            `Need to get ${Math.floor(Math.random() * 5000)}kB of archives.`,
            `Get:1 http://archive.ubuntu.com/ubuntu focal/main amd64 ${pkg} amd64 1.0 [${Math.floor(Math.random() * 1000)}kB]`
          ]);
          
          setTimeout(() => {
            addOutput([
              `Fetched ${Math.floor(Math.random() * 5000)}kB in 2s`,
              `Unpacking ${pkg}...`,
              `Setting up ${pkg}...`
            ]);
            
            setTimeout(() => {
              setInstalledPackages(prev => [...prev, pkg]);
              addOutput([`Processing triggers...`, `Done.`]);
              resolve();
            }, 1000);
          }, 1500);
        });
      } else if (subCmd === 'remove' && args.length > 1) {
        const pkg = args[1];
        if (!installedPackages.includes(pkg)) {
          return [`Package '${pkg}' is not installed`];
        }
        setInstalledPackages(prev => prev.filter(p => p !== pkg));
        return [`Removing ${pkg}...`, `Done.`];
      }
      return ['Usage: apt [install|remove|list|update] <package>'];
    },
    npm: (args) => {
      if (args.length === 0) return ['Usage: npm [install|uninstall|list|init] <package>'];
      const subCmd = args[0];
      
      if (subCmd === 'init') {
        return new Promise((resolve) => {
          addOutput([`This utility will walk you through creating a package.json file.`]);
          setTimeout(() => {
            setNode(resolvePath('package.json'), {
              type: 'file',
              content: JSON.stringify({ name: 'my-project', version: '1.0.0' }, null, 2),
              permissions: 'rw-r--r--'
            });
            addOutput([`Wrote to package.json`]);
            resolve();
          }, 500);
        });
      }
      
      if (subCmd === 'list' || subCmd === 'ls') {
        const npmPackages = installedPackages.filter(p => p.startsWith('npm:'));
        return npmPackages.length > 0 
          ? npmPackages.map(p => `├── ${p.replace('npm:', '')}@latest`)
          : ['(empty)'];
      } else if (subCmd === 'install' && args.length > 1) {
        const pkg = args[1];
        const fullPkg = `npm:${pkg}`;
        if (installedPackages.includes(fullPkg)) {
          return [`up to date, audited 1 package in 0.5s`];
        }
        
        return new Promise((resolve) => {
          addOutput([``, `added 1 package, and audited 2 packages in ${(Math.random() * 3 + 1).toFixed(1)}s`]);
          setTimeout(() => {
            setInstalledPackages(prev => [...prev, fullPkg]);
            addOutput([`found 0 vulnerabilities`]);
            resolve();
          }, 1200);
        });
      } else if (subCmd === 'uninstall' && args.length > 1) {
        const pkg = args[1];
        const fullPkg = `npm:${pkg}`;
        if (!installedPackages.includes(fullPkg)) {
          return [`npm ERR! Cannot find module '${pkg}'`];
        }
        setInstalledPackages(prev => prev.filter(p => p !== fullPkg));
        return [`removed 1 package in 0.4s`];
      }
      return ['Usage: npm [install|uninstall|list|init] <package>'];
    },
    pip: (args) => {
      if (args.length === 0) return ['Usage: pip [install|uninstall|list] <package>'];
      const subCmd = args[0];
      
      if (subCmd === 'list') {
        const pipPackages = installedPackages.filter(p => p.startsWith('pip:'));
        return pipPackages.length > 0
          ? ['Package    Version', '---------- -------', ...pipPackages.map(p => `${p.replace('pip:', '').padEnd(10)} ${(Math.random() * 10).toFixed(1)}.0`)]
          : ['(empty)'];
      } else if (subCmd === 'install' && args.length > 1) {
        const pkg = args[1];
        const fullPkg = `pip:${pkg}`;
        if (installedPackages.includes(fullPkg)) {
          return [`Requirement already satisfied: ${pkg}`];
        }
        
        return new Promise((resolve) => {
          const version = `${Math.floor(Math.random() * 10)}.${Math.floor(Math.random() * 10)}.${Math.floor(Math.random() * 10)}`;
          addOutput([
            `Collecting ${pkg}`,
            `  Downloading ${pkg}-${version}-py3-none-any.whl (${Math.floor(Math.random() * 500)} kB)`,
            `     |████████████████████████████████| ${Math.floor(Math.random() * 500)} kB 1.2 MB/s`
          ]);
          
          setTimeout(() => {
            setInstalledPackages(prev => [...prev, fullPkg]);
            addOutput([`Installing collected packages: ${pkg}`, `Successfully installed ${pkg}-${version}`]);
            resolve();
          }, 1800);
        });
      } else if (subCmd === 'uninstall' && args.length > 1) {
        const pkg = args[1];
        const fullPkg = `pip:${pkg}`;
        if (!installedPackages.includes(fullPkg)) {
          return [`WARNING: Skipping ${pkg} as it is not installed.`];
        }
        setInstalledPackages(prev => prev.filter(p => p !== fullPkg));
        return [`Successfully uninstalled ${pkg}`];
      }
      return ['Usage: pip [install|uninstall|list] <package>'];
    },
    ps: () => [
      'PID TTY          TIME CMD',
      '  1 pts/0    00:00:00 bash',
      '  2 pts/0    00:00:01 web-terminal',
      ' 42 pts/0    00:00:00 ps'
    ],
    top: () => [
      'top - 12:34:56 up 1 day, 2:30, 1 user',
      'Tasks: 3 total, 1 running, 2 sleeping',
      'CPU: 5.2% user, 2.1% system',
      'Memory: 512M total, 256M used, 256M free',
      '',
      'PID USER      CPU% MEM%   TIME COMMAND',
      '  1 guest      0.0  0.1   0:00 bash',
      '  2 guest      2.1  1.5   0:01 web-terminal'
    ],
    df: (args) => [
      'Filesystem     1K-blocks    Used Available Use% Mounted on',
      '/dev/sda1       10485760 5242880   5242880  50% /',
      'tmpfs             524288   52428    471860  10% /tmp'
    ],
    free: () => [
      '              total        used        free      shared',
      'Mem:         524288      262144      262144        1024',
      'Swap:        524288           0      524288'
    ],
    grep: (args) => {
      if (args.length < 2) return ['grep: missing pattern or file'];
      const pattern = args[0];
      const fileName = args[1];
      const node = getNode(resolvePath(fileName));
      
      if (!node || node.type !== 'file') return [`grep: ${fileName}: No such file`];
      
      const lines = (node.content || '').split('\n');
      return lines.filter(line => line.includes(pattern));
    },
    find: (args) => {
      const path = args[0] || '.';
      const node = getNode(resolvePath(path));
      
      if (!node) return [`find: '${path}': No such file or directory`];
      
      const results = [];
      const traverse = (n, p) => {
        results.push(p);
        if (n.type === 'dir' && n.contents) {
          Object.entries(n.contents).forEach(([name, child]) => {
            traverse(child, `${p}/${name}`);
          });
        }
      };
      traverse(node, path);
      return results;
    },
    head: (args) => {
      const n = args.includes('-n') ? parseInt(args[args.indexOf('-n') + 1]) : 10;
      const file = args.find(a => !a.startsWith('-') && a !== args[args.indexOf('-n') + 1]);
      
      if (!file) return ['head: missing file operand'];
      const node = getNode(resolvePath(file));
      if (!node || node.type !== 'file') return [`head: ${file}: No such file`];
      
      return (node.content || '').split('\n').slice(0, n);
    },
    tail: (args) => {
      const n = args.includes('-n') ? parseInt(args[args.indexOf('-n') + 1]) : 10;
      const file = args.find(a => !a.startsWith('-') && a !== args[args.indexOf('-n') + 1]);
      
      if (!file) return ['tail: missing file operand'];
      const node = getNode(resolvePath(file));
      if (!node || node.type !== 'file') return [`tail: ${file}: No such file`];
      
      const lines = (node.content || '').split('\n');
      return lines.slice(-n);
    },
    wc: (args) => {
      if (args.length === 0) return ['wc: missing file operand'];
      const node = getNode(resolvePath(args[0]));
      
      if (!node || node.type !== 'file') return [`wc: ${args[0]}: No such file`];
      
      const content = node.content || '';
      const lines = content.split('\n').length;
      const words = content.split(/\s+/).filter(Boolean).length;
      const chars = content.length;
      
      return [`  ${lines}  ${words}  ${chars} ${args[0]}`];
    },
    nano: (args) => {
      if (args.length === 0) return ['nano: missing file name'];
      return [`GNU nano 4.8 - Editing is not available in web terminal. Use 'echo "content" > ${args[0]}' instead.`];
    },
    history: () => commandHistory.map((cmd, i) => `  ${i + 1}  ${cmd}`),
    calc: (args) => {
      if (args.length === 0) return ['calc: missing expression'];
      try {
        const expr = args.join(' ').replace(/[^0-9+\-*/().]/g, '');
        const result = Function(`'use strict'; return (${expr})`)();
        return [`${result}`];
      } catch (e) {
        return ['calc: invalid expression'];
      }
    },
    weather: () => [
      '🌤️  Weather in Tokyo:',
      '   Temperature: 12°C',
      '   Conditions: Partly Cloudy',
      '   Humidity: 65%',
      '   Wind: 10 km/h NE'
    ]
  };

  const executeCommand = (cmd) => {
    const trimmed = cmd.trim();
    if (!trimmed) return;

    setHistory(prev => [...prev, { type: 'input', content: `${currentPath} $ ${trimmed}` }]);
    setCommandHistory(prev => [...prev, trimmed]);
    setHistoryIndex(-1);

    const parts = trimmed.split(' ');
    const command = parts[0];
    const args = parts.slice(1);

    if (commands[command]) {
      const output = commands[command](args);
      
      if (output instanceof Promise) {
        output.then(() => {});
      } else if (output && output.length > 0) {
        setHistory(prev => [...prev, ...output.map(line => ({ type: 'output', content: line }))]);
      }
    } else {
      setHistory(prev => [...prev, { type: 'output', content: `Command not found: ${command}. Type 'help' for available commands.` }]);
    }

    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      executeCommand(input);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (commandHistory.length > 0) {
        const newIndex = historyIndex === -1 ? commandHistory.length - 1 : Math.max(0, historyIndex - 1);
        setHistoryIndex(newIndex);
        setInput(commandHistory[newIndex]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex !== -1) {
        const newIndex = historyIndex + 1;
        if (newIndex >= commandHistory.length) {
          setHistoryIndex(-1);
          setInput('');
        } else {
          setHistoryIndex(newIndex);
          setInput(commandHistory[newIndex]);
        }
      }
    } else if (e.key === 'Tab') {
      e.preventDefault();
      const cmdNames = Object.keys(commands);
      const matches = cmdNames.filter(c => c.startsWith(input));
      if (matches.length === 1) {
        setInput(matches[0]);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 p-4 flex items-center justify-center">
      <div className={`w-full max-w-4xl bg-gray-800 rounded-lg shadow-2xl overflow-hidden transition-all ${isMinimized ? 'h-12' : 'h-[600px]'}`}>
        <div className="bg-gray-700 px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-5 h-5 text-green-400" />
            <span className="text-green-400 font-mono text-sm">Web Terminal v2.0</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="text-gray-400 hover:text-white transition-colors"
            >
              {isMinimized ? <Maximize2 className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {!isMinimized && (
          <div
            ref={terminalRef}
            onClick={() => inputRef.current?.focus()}
            className="h-[552px] p-4 overflow-y-auto font-mono text-sm bg-gray-900 cursor-text"
          >
            {history.map((item, i) => (
              <div key={i} className={item.type === 'input' ? 'text-green-400' : 'text-gray-300'}>
                {item.content}
              </div>
            ))}
            
            <div className="flex items-center gap-2 text-green-400">
              <span>{currentPath} $</span>
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                className="flex-1 bg-transparent outline-none text-gray-300"
                autoFocus
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
