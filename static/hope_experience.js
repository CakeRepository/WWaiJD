/**
 * WWAIJD - Living 3D WebGL Background Engine
 * Continuously renders a 3D universe of Hope, Sight, Light Petals, the Cross, and the Trinity.
 * Powered by Three.js
 */

document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('hopeCanvas');
    if (!canvas) return;

    // Controls elements on page
    const phaseBtns = document.querySelectorAll('.hope-phase-btn');
    const storyBox = document.getElementById('hopeStoryText');

    // 3D Scene setup variables
    let scene, camera, renderer;
    let stars = [];
    let petals = [];
    let lines = [];
    let agencyParticles = [];
    let trinityParticles = [];
    let cursorPosition3D = new THREE.Vector3(0, 0, -80);
    let targetCameraPos = new THREE.Vector3(0, 0, 45);
    let currentCameraPos = new THREE.Vector3(0, 0, 45);
    let mouse = { x: 0, y: 0, isDown: false };
    
    // State variables
    let activePhase = 1; // 0: Blindness, 1: Sight (Default live background), 2: Crucifixion, 3: Triune Hope
    const starCount = 30;
    const petalCount = 45;
    const depthZ = -80;

    let starsGroup, petalsGroup, crossGroup, trinityGroup;
    let trinityLights = [];
    let clock = new THREE.Clock();

    // Story text map
    const phaseStories = {
        0: '<strong>Blindness & Despair:</strong> Hope requires Goals, Pathways, and Agency. In spiritual darkness, vision is dimmed, representing humanity seeking light.',
        1: '<strong>Sight Restored (Goals, Pathways & Agency):</strong> Christ touches the eyes. Glowing golden stars represent your <em>Goals</em>, your interactions activate <em>Agency</em>, and light beams trace <em>Pathways</em> across the page.',
        2: '<strong>The First Sight (The Crucifixion):</strong> The vision focuses into the cross of light. Where others saw despair, the restored eyes saw the ultimate miracle of love and redemption.',
        3: '<strong>The Triune Hope (Father, Son, Holy Spirit):</strong> Three orbital spheres of divine light (Sapphire, Gold, Emerald) weave through the background depth around the Cross.'
    };

    function initThreeJS() {
        // 1. Scene setup
        scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x040916, 0.006);

        // 2. Camera setup
        camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.copy(currentCameraPos);

        // 3. Renderer setup
        renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.1;

        // 4. Ambient & Point Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
        scene.add(ambientLight);

        const mainLight = new THREE.PointLight(0xf3c866, 1.8, 350);
        mainLight.position.set(0, 30, 40);
        scene.add(mainLight);

        // 5. Build 3D Elements
        createStars();
        createPetals(); // Floating light petals (inspired by floral background renders)
        createCross();
        createTrinityOrbits();

        // 6. Bind Document Events
        window.addEventListener('resize', onWindowResize);
        
        document.addEventListener('mousemove', (e) => {
            mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
            projectMouseTo3D();
        });

        document.addEventListener('mousedown', () => { mouse.isDown = true; });
        document.addEventListener('mouseup', () => { mouse.isDown = false; });

        // Bind Phase Buttons if present
        if (phaseBtns.length > 0) {
            phaseBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const phase = parseInt(btn.getAttribute('data-phase'));
                    setAtmospherePhase(phase);
                });
            });
        }

        // Start animation loop
        animate();
    }

    function createStars() {
        starsGroup = new THREE.Group();
        scene.add(starsGroup);

        const starGeometry = new THREE.SphereGeometry(0.75, 8, 8);
        const starMaterial = new THREE.MeshBasicMaterial({
            color: 0xf3c866,
            transparent: true,
            opacity: 0.9
        });

        for (let i = 0; i < starCount; i++) {
            const star = new THREE.Mesh(starGeometry, starMaterial.clone());
            star.position.set(
                (Math.random() - 0.5) * 180,
                (Math.random() - 0.5) * 120,
                depthZ + (Math.random() - 0.5) * 50
            );
            
            const s = 0.5 + Math.random() * 1.4;
            star.scale.set(s, s, s);

            star.userData = {
                pulseSpeed: 1 + Math.random() * 2.5,
                pulseOffset: Math.random() * Math.PI * 2,
                baseOpacity: 0.5 + Math.random() * 0.5
            };

            starsGroup.add(star);
            stars.push(star);
        }
    }

    function createPetals() {
        petalsGroup = new THREE.Group();
        scene.add(petalsGroup);

        // Petal shape curve
        const shape = new THREE.Shape();
        shape.moveTo(0, 0);
        shape.bezierCurveTo(0.5, 0.8, 1.2, 1.5, 0, 2.5);
        shape.bezierCurveTo(-1.2, 1.5, -0.5, 0.8, 0, 0);

        const geom = new THREE.ShapeGeometry(shape);
        geom.center();

        const petalColors = [0xf3c866, 0x6ce4d6, 0xffe8d6, 0x4da3ff];

        for (let i = 0; i < petalCount; i++) {
            const mat = new THREE.MeshBasicMaterial({
                color: petalColors[i % petalColors.length],
                transparent: true,
                opacity: 0.35 + Math.random() * 0.4,
                side: THREE.DoubleSide
            });

            const petal = new THREE.Mesh(geom, mat);
            
            // Scatter petals around workspace
            petal.position.set(
                (Math.random() - 0.5) * 160,
                (Math.random() - 0.5) * 140,
                depthZ + (Math.random() - 0.5) * 60
            );

            const scale = 0.6 + Math.random() * 0.9;
            petal.scale.set(scale, scale, scale);

            petal.userData = {
                speedY: 0.15 + Math.random() * 0.25, // Upward drift
                swaySpeed: 0.8 + Math.random() * 1.5,
                swayOffset: Math.random() * Math.PI * 2,
                rotSpeedX: (Math.random() - 0.5) * 0.02,
                rotSpeedY: (Math.random() - 0.5) * 0.02,
                rotSpeedZ: (Math.random() - 0.5) * 0.02
            };

            petalsGroup.add(petal);
            petals.push(petal);
        }
    }

    function createCross() {
        crossGroup = new THREE.Group();
        crossGroup.position.set(0, 5, depthZ);
        scene.add(crossGroup);

        const crossMaterial = new THREE.MeshBasicMaterial({
            color: 0xfdf5e3,
            transparent: true,
            opacity: 0.85
        });

        const haloMaterial = new THREE.MeshBasicMaterial({
            color: 0xf3c866,
            transparent: true,
            opacity: 0.45,
            side: THREE.DoubleSide
        });

        // Vertical beam
        const verticalGeom = new THREE.BoxGeometry(1.6, 32, 1.6);
        const verticalBeam = new THREE.Mesh(verticalGeom, crossMaterial);
        verticalBeam.position.y = 4;
        crossGroup.add(verticalBeam);

        // Horizontal beam
        const horizontalGeom = new THREE.BoxGeometry(18, 1.6, 1.6);
        const horizontalBeam = new THREE.Mesh(horizontalGeom, crossMaterial);
        horizontalBeam.position.y = 11;
        crossGroup.add(horizontalBeam);

        // Halo circle
        const haloGeom = new THREE.RingGeometry(4.0, 4.4, 32);
        const halo = new THREE.Mesh(haloGeom, haloMaterial);
        halo.position.set(0, 11, 0.1);
        crossGroup.add(halo);

        crossGroup.userData = {
            verticalBeam: verticalBeam,
            horizontalBeam: horizontalBeam,
            halo: halo,
            opacity: 0.85,
            targetOpacity: 0.85
        };
    }

    function createTrinityOrbits() {
        trinityGroup = new THREE.Group();
        trinityGroup.position.set(0, 5, depthZ);
        scene.add(trinityGroup);

        const colors = [0x4da3ff, 0xfdf5e3, 0x6ce4d6];
        
        for (let i = 0; i < 3; i++) {
            const lightGroup = new THREE.Group();
            
            const sphereGeom = new THREE.SphereGeometry(0.7, 16, 16);
            const sphereMat = new THREE.MeshBasicMaterial({
                color: colors[i],
                transparent: true,
                opacity: 0.95
            });
            const mesh = new THREE.Mesh(sphereGeom, sphereMat);
            lightGroup.add(mesh);

            const pLight = new THREE.PointLight(colors[i], 1.5, 60);
            lightGroup.add(pLight);

            trinityGroup.add(lightGroup);
            trinityLights.push({
                group: lightGroup,
                mesh: mesh,
                light: pLight,
                color: colors[i],
                angle: (i * Math.PI * 2) / 3
            });
        }
    }

    function projectMouseTo3D() {
        if (!camera) return;
        const tempV = new THREE.Vector3(mouse.x, mouse.y, 0.5);
        tempV.unproject(camera);
        
        const dir = tempV.sub(camera.position).normalize();
        const distance = (depthZ - camera.position.z) / dir.z;
        cursorPosition3D.copy(camera.position).add(dir.multiplyScalar(distance));
    }

    function spawnAgencyParticles() {
        if (activePhase === 0) return;

        const count = mouse.isDown ? 4 : 1;
        const geom = new THREE.SphereGeometry(0.25 + Math.random() * 0.2, 4, 4);
        const mat = new THREE.MeshBasicMaterial({
            color: 0x6ce4d6, // Teal stardust
            transparent: true,
            opacity: 0.85
        });

        for (let i = 0; i < count; i++) {
            const mesh = new THREE.Mesh(geom, mat);
            mesh.position.copy(cursorPosition3D).add(new THREE.Vector3(
                (Math.random() - 0.5) * 4,
                (Math.random() - 0.5) * 4,
                (Math.random() - 0.5) * 4
            ));

            const particle = {
                mesh: mesh,
                velocity: new THREE.Vector3(
                    (Math.random() - 0.5) * 3,
                    (Math.random() - 0.5) * 3 + 1.5,
                    (Math.random() - 0.5) * 3
                ),
                age: 0,
                maxAge: 35 + Math.random() * 35
            };

            scene.add(mesh);
            agencyParticles.push(particle);
        }
    }

    function spawnTrinityTrail(position, colorHex) {
        const geom = new THREE.SphereGeometry(0.18, 4, 4);
        const mat = new THREE.MeshBasicMaterial({
            color: colorHex,
            transparent: true,
            opacity: 0.75
        });

        const mesh = new THREE.Mesh(geom, mat);
        mesh.position.copy(position).add(new THREE.Vector3(
            (Math.random() - 0.5) * 0.6,
            (Math.random() - 0.5) * 0.6,
            (Math.random() - 0.5) * 0.6
        ));

        const particle = {
            mesh: mesh,
            velocity: new THREE.Vector3(
                (Math.random() - 0.5) * 0.6,
                (Math.random() - 0.5) * 0.6,
                (Math.random() - 0.5) * 0.6
            ),
            age: 0,
            maxAge: 25 + Math.random() * 25
        };

        scene.add(mesh);
        trinityParticles.push(particle);
    }

    function updatePathways() {
        lines.forEach(l => scene.remove(l));
        lines = [];

        if (activePhase === 0) return;

        // Calculate distances from cursorPosition3D to all stars
        const distances = stars.map(s => ({
            star: s,
            dist: cursorPosition3D.distanceTo(s.position)
        }));

        distances.sort((a, b) => a.dist - b.dist);

        const connectionsCount = Math.min(3, distances.length);
        const maxDrawDistance = 90;

        for (let i = 0; i < connectionsCount; i++) {
            const targetStar = distances[i].star;
            const dist = distances[i].dist;
            
            if (dist > maxDrawDistance) continue;

            const start = cursorPosition3D.clone();
            const end = targetStar.position.clone();
            const mid = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
            mid.y += Math.sin(clock.getElapsedTime() * 2 + i) * 8;

            const curve = new THREE.QuadraticBezierCurve3(start, mid, end);
            const points = curve.getPoints(12);
            
            const lineGeom = new THREE.BufferGeometry().setFromPoints(points);
            const opacity = (1.0 - (dist / maxDrawDistance)) * 0.6;

            const lineMat = new THREE.LineBasicMaterial({
                color: 0x4da3ff,
                transparent: true,
                opacity: opacity
            });

            const lineMesh = new THREE.Line(lineGeom, lineMat);
            scene.add(lineMesh);
            lines.push(lineMesh);
        }
    }

    function animate() {
        requestAnimationFrame(animate);

        const delta = clock.getDelta();
        const time = clock.getElapsedTime();

        // 1. Animate Floating Light Petals
        petals.forEach(p => {
            p.position.y += p.userData.speedY;
            p.position.x += Math.sin(time * p.userData.swaySpeed + p.userData.swayOffset) * 0.1;
            
            p.rotation.x += p.userData.rotSpeedX;
            p.rotation.y += p.userData.rotSpeedY;
            p.rotation.z += p.userData.rotSpeedZ;

            // Reset when floating out of top bound
            if (p.position.y > 80) {
                p.position.y = -80;
                p.position.x = (Math.random() - 0.5) * 160;
            }
        });

        // 2. Animate Star Pulsing
        stars.forEach(star => {
            const scaleOffset = Math.sin(time * star.userData.pulseSpeed + star.userData.pulseOffset) * 0.15;
            const currentScale = 0.8 + scaleOffset;
            star.scale.set(currentScale, currentScale, currentScale);
            
            star.material.opacity = activePhase > 0 ? 
                star.userData.baseOpacity + Math.sin(time * 2 + star.userData.pulseOffset) * 0.15 : 0.05;
        });

        // 3. Camera Position Lerp
        currentCameraPos.lerp(targetCameraPos, 0.04);
        camera.position.copy(currentCameraPos);

        // Parallax mouse effect on camera
        camera.position.x += (mouse.x * 6 - camera.position.x) * 0.02;
        camera.position.y += (mouse.y * 4 - camera.position.y) * 0.02;
        camera.lookAt(new THREE.Vector3(0, 3, depthZ));

        // 4. Mouse Agency particles
        if (activePhase > 0) {
            spawnAgencyParticles();
        }

        for (let i = agencyParticles.length - 1; i >= 0; i--) {
            const p = agencyParticles[i];
            p.age++;
            p.mesh.position.addScaledVector(p.velocity, delta);
            p.velocity.multiplyScalar(0.95);
            p.mesh.material.opacity = 1.0 - (p.age / p.maxAge);
            
            if (p.age >= p.maxAge) {
                scene.remove(p.mesh);
                p.mesh.geometry.dispose();
                p.mesh.material.dispose();
                agencyParticles.splice(i, 1);
            }
        }

        // 5. Constellation Pathways
        updatePathways();

        // 6. Cross & Halo rotation
        if (crossGroup && crossGroup.userData) {
            const crossData = crossGroup.userData;
            crossData.opacity = THREE.MathUtils.lerp(crossData.opacity, crossData.targetOpacity, 0.05);
            crossData.verticalBeam.material.opacity = crossData.opacity;
            crossData.horizontalBeam.material.opacity = crossData.opacity;
            crossData.halo.material.opacity = crossData.opacity * 0.6;
            crossData.halo.rotation.z += 0.005;
        }

        // 7. Trinity Orbits Animation
        trinityLights.forEach(tLight => {
            let targetOpacity = activePhase === 0 ? 0.0 : 0.9;
            let targetIntensity = activePhase === 0 ? 0.0 : 1.5;
            
            tLight.angle += delta * 0.9;
            
            const rHorizontal = 24;
            const rVertical = 16;
            let x = 0, y = 0, z = 0;

            if (tLight.color === 0x4da3ff) { // Father (Elliptical X-Y)
                x = Math.cos(tLight.angle) * rHorizontal;
                y = Math.sin(tLight.angle) * rVertical + 11;
                z = Math.sin(tLight.angle) * 12;
            } else if (tLight.color === 0xfdf5e3) { // Son (Elliptical Y-Z)
                x = Math.cos(tLight.angle) * 10;
                y = Math.sin(tLight.angle) * rHorizontal + 11;
                z = Math.cos(tLight.angle) * rVertical;
            } else { // Holy Spirit (Elliptical X-Z)
                x = Math.cos(tLight.angle) * rHorizontal;
                y = Math.cos(tLight.angle * 0.5) * 8 + 11;
                z = Math.sin(tLight.angle) * rVertical;
            }

            tLight.group.position.set(x, y, z);
            
            if (activePhase > 0) {
                const worldPos = new THREE.Vector3();
                tLight.mesh.getWorldPosition(worldPos);
                spawnTrinityTrail(worldPos, tLight.color);
            }
            
            tLight.mesh.material.opacity = THREE.MathUtils.lerp(tLight.mesh.material.opacity, targetOpacity, 0.05);
            tLight.light.intensity = THREE.MathUtils.lerp(tLight.light.intensity, targetIntensity, 0.05);
        });

        // Update trinity trails
        for (let i = trinityParticles.length - 1; i >= 0; i--) {
            const p = trinityParticles[i];
            p.age++;
            p.mesh.position.addScaledVector(p.velocity, delta);
            p.mesh.material.opacity = (1.0 - (p.age / p.maxAge)) * 0.75;
            
            if (p.age >= p.maxAge) {
                scene.remove(p.mesh);
                p.mesh.geometry.dispose();
                p.mesh.material.dispose();
                trinityParticles.splice(i, 1);
            }
        }

        renderer.render(scene, camera);
    }

    function onWindowResize() {
        if (!camera || !renderer) return;
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    }

    function setAtmospherePhase(phaseNum) {
        activePhase = phaseNum;

        // Update buttons state
        phaseBtns.forEach(btn => {
            btn.classList.remove('is-active');
            if (parseInt(btn.getAttribute('data-phase')) === phaseNum) {
                btn.classList.add('is-active');
            }
        });

        // Update story description
        if (storyBox && phaseStories[phaseNum]) {
            storyBox.style.opacity = 0;
            setTimeout(() => {
                storyBox.innerHTML = phaseStories[phaseNum];
                storyBox.style.opacity = 1;
            }, 250);
        }

        // Adjust camera & scene objects according to phase
        if (phaseNum === 0) { // Blindness
            canvas.classList.add('is-blind');
            targetCameraPos.set(0, 0, 75);
            if (crossGroup) crossGroup.userData.targetOpacity = 0.1;
        } else if (phaseNum === 1) { // Sight
            canvas.classList.remove('is-blind');
            targetCameraPos.set(0, 0, 45);
            if (crossGroup) crossGroup.userData.targetOpacity = 0.85;
        } else if (phaseNum === 2) { // Crucifixion focus
            canvas.classList.remove('is-blind');
            targetCameraPos.set(0, 8, -25);
            if (crossGroup) crossGroup.userData.targetOpacity = 1.0;
        } else if (phaseNum === 3) { // Triune Hope
            canvas.classList.remove('is-blind');
            targetCameraPos.set(0, 0, 35);
            if (crossGroup) crossGroup.userData.targetOpacity = 1.0;
        }
    }

    // Initialize scene
    initThreeJS();
});
